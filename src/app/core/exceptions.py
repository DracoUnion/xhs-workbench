"""业务错误体系：统一持有 code + message + details，供 API 层与 Agent 层复用。"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """业务异常基类。code 用于前端与审计定位，details 用于结构化补述。"""

    default_message = "业务处理失败"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.__class__.__name__
        self.details = details or []


class AuthError(AppError):
    default_message = "认证失败"


class PermissionError(AppError):
    """仅覆盖框架内置 PermissionError 同名，语义为「越权」。"""
    default_message = "无权限执行该操作"


class NotFoundError(AppError):
    default_message = "资源不存在"


class DeviceBusyError(AppError):
    default_message = "设备被另一任务占用"


class ConcurrencyError(AppError):
    default_message = "同 Scope 已有在途任务"


class ProductValidationError(AppError):
    default_message = "商品采集校验未通过"


class ReviewRequired(AppError):
    """Agent 运行中抛出的检查点请求；编排引擎捕获后置 BLOCKED 并落 review_points。"""

    default_message = "需要人工审核/介入"

    def __init__(
        self,
        rtype: str = "REVIEW",
        payload: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.rtype = rtype
        self.payload = payload or {}


class LlmError(AppError):
    """LLM 调用失败，可按 kind 细分（timeout / rate_limit / bad_request）。"""

    default_message = "LLM 调用失败"

    def __init__(self, *, kind: str = "unknown", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.kind = kind


# ---------- 可重试与致命异常 ----------


class RecoverableError(AppError):
    """采集/网络类可重试错误；编排引擎内做指数退避重试。"""

    default_message = "可重试错误"


class TranscriptionError(AppError):
    default_message = "视频转写失败"


class FatalError(AppError):
    """不可重试错误：Run 直接置 failed 并告警。"""

    default_message = "致命错误"


# ---------- 错误码 → HTTP 状态 ----------

HTTP_STATUS_BY_CODE: dict[str, int] = {
    "AUTH_REQUIRED": 401,
    "TOKEN_INVALID": 401,
    "AUTH_FAILED": 401,
    "PERMISSION_DENIED": 403,
    "RESOURCE_NOT_FOUND": 404,
    "AGENT_NOT_FOUND": 404,
    "DEVICE_BUSY": 409,
    "AGENT_RUN_IN_PROGRESS": 409,
    "TASK_STATE_CONFLICT": 409,
    "REVIEW_ALREADY_ACTED": 409,
    "PRODUCT_VALIDATION_FAILED": 422,
    "SKILL_NOT_ACTIVE": 422,
    "VALIDATION_ERROR": 422,
    "OPENAI_NOT_CONFIGURED": 502,
    "OPENAI_CALL_FAILED": 502,
    "OPENAI_BAD_REQUEST": 502,
    "OPENAI_RATE_LIMIT": 429,
}