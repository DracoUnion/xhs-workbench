"""任务中心路由：发起、查询、恢复、终止。"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models import AgentRun, User
from app.services.runs import (
    abort_run,
    get_run,
    list_runs,
    resume_run,
    run_to_dict,
    submit_run,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    agent_key: str = Field(..., description="Agent 定义 key，见 agent_defs")
    product_id: int | None = None
    context: str | None = Field(default=None, description="初始上下文/任务描述")


class TaskCreatedResp(BaseModel):
    run_id: int
    run_uuid: str
    mode: Literal["celery", "inline"]


@router.get("")
def list_tasks(
    status: str | None = Query(default=None),
    agent_key: str | None = Query(default=None),
    product_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    items, total = list_runs(
        db, status=status, agent_key=agent_key, product_id=product_id,
        page=page, page_size=page_size,
    )
    return {"data": items, "meta": {"total": total, "page": page, "page_size": page_size}}


@router.get("/{run_id}")
def get_task(run_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> dict:
    return {"data": run_to_dict(get_run(db, run_id))}


@router.get("/{run_id}/messages")
def get_task_messages(run_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> dict:
    run: AgentRun = get_run(db, run_id)
    return {"data": run.messages, "tool_calls": run.tool_calls}


@router.post("", status_code=202)
def create_task(
    body: CreateTaskRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return submit_run(db, body.agent_key, product_id=body.product_id, context=body.context)


@router.post("/{run_id}/resume")
def resume(run_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> dict:
    mode = resume_run(db, run_id)
    return {"data": {"run_id": run_id, "mode": mode}}


@router.post("/{run_id}/abort")
def abort(run_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> dict:
    return {"data": abort_run(db, run_id)}