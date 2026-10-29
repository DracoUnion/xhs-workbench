"""任务层。

- ``celery_app.py`` / ``runs.py``：Celery 任务与 inline 执行（业务运行权威路径）。
- ``task.py``：通用零 Qt Task/TaskManager 状态机，供 UI 桥使用（与 run 调度并存）。
"""
from __future__ import annotations

from tasks.task import Task, TaskCancelled, TaskManager, TaskState

__all__ = ["Task", "TaskState", "TaskManager", "TaskCancelled"]