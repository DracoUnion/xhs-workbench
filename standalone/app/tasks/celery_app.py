"""Celery 应用。broker 未就绪时仅构造配置对象，不主动连接；由 .delay() 触达。"""
from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

s = get_settings()

celery_app = Celery("xhs", broker=s.broker_url, backend=s.result_backend)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    # 结果默认不落 Redis，前端进度以 WS/落库为准
    task_ignore_result=True,
)

# 任务自动发现
celery_app.conf.include = ["app.tasks.runs"]