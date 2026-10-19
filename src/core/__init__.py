"""基础设施快捷入口：汇总下层模块，供 services/agents/main 导入。"""
from core.config import Settings, get_settings
from core.database import Base, SessionLocal, engine, get_db, metadata
from core.events import DomainEvent, EventBus, get_bus
from core.exceptions import (
    AppError,
    AuthError,
    ConcurrencyError,
    DeviceBusyError,
    FatalError,
    HTTP_STATUS_BY_CODE,
    LlmError,
    NotFoundError,
    PermissionError,
    ProductValidationError,
    RecoverableError,
    ReviewRequired,
    TranscriptionError,
)
from core.logging import get_logger, setup_logging
from core.ws_manager import ws_manager
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_kind,
    verify_password,
)

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "metadata",
    "Settings",
    "get_settings",
    "DomainEvent",
    "EventBus",
    "get_bus",
    "AppError",
    "AuthError",
    "PermissionError",
    "NotFoundError",
    "DeviceBusyError",
    "ConcurrencyError",
    "ProductValidationError",
    "ReviewRequired",
    "LlmError",
    "RecoverableError",
    "TranscriptionError",
    "FatalError",
    "get_logger",
    "setup_logging",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "token_kind",
    "hash_password",
    "verify_password",
    "HTTP_STATUS_BY_CODE",
    "ws_manager",
]