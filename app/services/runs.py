"""运行服务：AgentRun 的 DB 存取、状态流转与任务派发（celery 或 inline 线程）。"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Thread
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.runtime import AgentMeta, AgentRuntime, RunState
from app.core.config import get_settings
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.core.ws_manager import ws_manager
from app.models import AgentDef, AgentRun, ReviewPoint

logger = get_logger("runs")

ST_PENDING = "pending"
ST_RUNNING = "running"
ST_BLOCKED = "blocked"
ST_DONE = "done"
ST_FAILED = "failed"
ST_KILLED = "killed"

TERMINAL = {ST_DONE, ST_FAILED, ST_KILLED}
NON_RESUMABLE = TERMINAL | {ST_BLOCKED}


class DbRunStore:
    """将 AgentRuntime 的持久化协议落地到 AgentRun / ReviewPoint 表。"""

    def __init__(self, db: Session, run: AgentRun) -> None:
        self.db = db
        self.run = run

    def load(self) -> RunState:
        r = self.run
        return RunState(
            status=r.status,
            messages=r.messages,
            tool_calls=r.tool_calls,
            checkpoint=r.checkpoint,
            result=r.result,
            error=r.error,
        )

    def persist(self, state: RunState) -> None:
        r = self.run
        r.status = state.status
        r.messages = state.messages
        r.tool_calls = state.tool_calls
        r.checkpoint = state.checkpoint
        r.result = state.result
        r.error = state.error
        now = datetime.now(timezone.utc)
        if state.status == ST_RUNNING and r.started_at is None:
            r.started_at = now
        if state.status in TERMINAL:
            r.finished_at = now
        self.db.commit()

    def create_review_point(self, rtype: str, payload: Any) -> Any:
        point = ReviewPoint(
            run_id=self.run.id,
            agent_key=self.run.agent_key,
            rtype=rtype,
            payload=payload or {},
            action="pending",
        )
        self.db.add(point)
        self.db.commit()
        self.db.refresh(point)
        return point.id


# ---------- 查询 ----------


def run_to_dict(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "run_uuid": str(run.run_uuid),
        "agent_key": run.agent_key,
        "product_id": run.product_id,
        "status": run.status,
        "result": run.result,
        "error": run.error,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "continue_at": run.continue_at,
        "created_at": run.created_at,
    }


def list_runs(
    db: Session,
    *,
    status: str | None = None,
    agent_key: str | None = None,
    product_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    conds = []
    if status:
        conds.append(AgentRun.status == status)
    if agent_key:
        conds.append(AgentRun.agent_key == agent_key)
    if product_id is not None:
        conds.append(AgentRun.product_id == product_id)
    base = select(AgentRun)
    if conds:
        base = base.where(*conds)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    runs = db.scalars(
        base.order_by(AgentRun.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return [run_to_dict(r) for r in runs], total


def get_run(db: Session, run_id: int) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise NotFoundError(code="RESOURCE_NOT_FOUND", message=f"任务不存在: {run_id}")
    return run


# ---------- 发起 / 流转 ----------


def _get_agent_def(db: Session, agent_key: str) -> AgentDef:
    ag = db.scalar(
        select(AgentDef).where(AgentDef.key == agent_key, AgentDef.is_enabled.is_(True))
    )
    if ag is None:
        raise NotFoundError(
            code="AGENT_NOT_FOUND", message=f"Agent 不存在或未启用: {agent_key}"
        )
    return ag


def create_run(
    db: Session, agent_key: str, product_id: int | None = None, context: str | None = None
) -> AgentRun:
    ag = _get_agent_def(db, agent_key)
    messages: list[dict] = [{"role": "user", "content": context}] if context else []
    run = AgentRun(agent_key=ag.key, product_id=product_id, status=ST_PENDING, messages=messages)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _event_sink(run_id: int):
    def sink(event: dict) -> None:
        data = dict(event.get("data", {}))
        data.setdefault("run_id", run_id)
        ws_manager.broadcast_sync({"type": event.get("type"), "data": data})

    return sink


def _build_and_run(run_id: int) -> RunState | None:
    """以独立 Session 加载 Run 并执行 Agent 循环（供 inline 线程与 Celery 复用）。"""
    from app.adapters.llm import get_llm_provider
    from app.core.database import SessionLocal
    from app.tools import registry

    with SessionLocal() as db:
        try:
            run = db.get(AgentRun, run_id)
            if run is None:
                logger.warning("run missing while executing", run_id=run_id)
                return None
            ag = db.scalar(select(AgentDef).where(AgentDef.key == run.agent_key))
            if ag is None:
                logger.error("agent def missing", run_id=run_id, agent=run.agent_key)
                run.status = ST_FAILED
                db.commit()
                return None
            meta = AgentMeta(
                system_prompt=ag.system_prompt,
                model=ag.model,
                temperature=float(ag.temperature),
                tool_keys=ag.tool_keys or [],
            )
            store = DbRunStore(db, run)
            runtime = AgentRuntime(
                provider=get_llm_provider(),
                tools_registry=registry,
                store=store,
                sink=_event_sink(run_id),
            )
            return runtime.run(meta)
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent run crashed", run_id=run_id)
            run = db.get(AgentRun, run_id)
            if run is not None and run.status not in TERMINAL:
                run.status = ST_FAILED
                run.error = {"code": "RUN_CRASH", "message": str(exc)}
                db.commit()
            return None


def _run_inline_wrapper(run_id: int) -> None:
    try:
        _build_and_run(run_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("inline runner unexpected", run_id=run_id, error=str(exc))


def _dispatch(run_id: int) -> str:
    """按配置派发；celery 不可用时回退 inline 线程。"""
    s = get_settings()
    if s.run_executor == "celery":
        try:
            from app.tasks.runs import run_agent_task

            run_agent_task.delay(run_id)
            return "celery"
        except Exception as exc:  # noqa: BLE001
            logger.warning("celery unavailable, fallback inline", error=str(exc))
    t = Thread(target=_run_inline_wrapper, args=(run_id,), daemon=True)
    t.start()
    return "inline"


def submit_run(
    db: Session, agent_key: str, product_id: int | None = None, context: str | None = None
) -> dict:
    run = create_run(db, agent_key, product_id, context)
    db.refresh(run)
    mode = _dispatch(run.id)
    return {"run_id": run.id, "run_uuid": str(run.run_uuid), "mode": mode}


def resume_run(db: Session, run_id: int) -> str:
    run = get_run(db, run_id)
    if run.status not in (ST_BLOCKED, ST_FAILED, ST_PENDING):
        raise AppError(
            code="TASK_STATE_CONFLICT",
            message=f"仅 blocked/failed/pending 状态可恢复，当前: {run.status}",
        )
    run.status = ST_PENDING
    run.error = None
    db.commit()
    return _dispatch(run_id)


def abort_run(db: Session, run_id: int, reason: str | None = None) -> dict:
    run = get_run(db, run_id)
    if run.status in TERMINAL:
        return run_to_dict(run)
    run.status = ST_KILLED
    run.error = {"code": "ABORTED", "message": reason or "用户终止"}
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return run_to_dict(run)


# ---------- 审核点 ----------

REVIEW_ACTION = {"passed", "rejected"}


def list_review_points(db: Session, *, pending_only: bool = True) -> list[dict]:
    q = select(ReviewPoint)
    if pending_only:
        q = q.where(ReviewPoint.action == "pending")
    points = db.scalars(q.order_by(ReviewPoint.id.desc()).limit(100)).all()
    return [
        {
            "id": p.id,
            "run_id": p.run_id,
            "agent_key": p.agent_key,
            "rtype": p.rtype,
            "payload": p.payload,
            "action": p.action,
            "created_at": p.created_at,
        }
        for p in points
    ]


def act_review_point(
    db: Session, point_id: int, action: str, note: str | None = None, actor_id: int | None = None
) -> dict:
    point = db.get(ReviewPoint, point_id)
    if point is None:
        raise NotFoundError(code="RESOURCE_NOT_FOUND", message=f"审核点不存在: {point_id}")
    if point.action != "pending":
        raise AppError(code="REVIEW_ALREADY_ACTED", message="该审核点已处理")
    if action not in REVIEW_ACTION:
        raise AppError(code="VALIDATION_ERROR", message=f"action 必须为 {'/'.join(sorted(REVIEW_ACTION))}")
    point.action = action
    point.action_by = actor_id
    point.action_note = note
    point.acted_at = datetime.now(timezone.utc)
    db.commit()

    resumed = None
    if action == "passed" and point.rtype in ("REVIEW", "MANUAL"):
        try:
            resumed = resume_run(db, point.run_id)
        except AppError as exc:
            logger.warning("resume after review failed", run_id=point.run_id, error=exc.code)
    return {
        "id": point.id,
        "action": point.action,
        "resumed": resumed,
        "run_id": point.run_id,
    }