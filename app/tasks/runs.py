"""Celery AgentRun 任务入口。"""
from __future__ import annotations

from app.tasks.celery_app import celery_app


@celery_app.task(name="agents.run_agent", bind=True)
def run_agent_task(_self, run_id: int) -> None:
    # 复用 inline runner：它会创建 worker 私有 Session，避免跨线程/进程复用连接。
    from app.services.runs import _run_inline_wrapper

    _run_inline_wrapper(run_id)