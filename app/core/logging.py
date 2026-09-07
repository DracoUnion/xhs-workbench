"""结构化日志：structlog 初始化，事件内注入 run_uuid/agent/device 等上下文。"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    s = get_settings()
    Path(s.log_dir).mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if s.debug else logging.INFO
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # bind_contextvars 注入的字段
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 打开 rotate 每日一档文件日志（粗粒度；结构化明细以 stdout 为主）
    _file_handler = logging.FileHandler(
        Path(s.log_dir) / "backend.log", encoding="utf-8"
    )
    _file_handler.setLevel(level)
    logging.getLogger().addHandler(_file_handler)


def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name=name)