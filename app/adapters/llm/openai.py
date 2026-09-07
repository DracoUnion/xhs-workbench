"""OpenAI Function Calling 实现：将 SDK 响应映射为 ChatResult，异常分类为 LlmError。"""
from __future__ import annotations

import json
from typing import Any, Sequence

from openai import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.adapters.llm import ChatResult, ToolCall
from app.core.config import get_settings
from app.core.exceptions import LlmError


class OpenAIProvider:
    """通过 OpenAI Chat Completions 的 tools 字段实现 Function Calling。"""

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.openai_api_key or None
        self._model = s.llm_model_default
        self._client = OpenAI(api_key=self._api_key) if self._api_key else None

    def chat(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> ChatResult:
        if self._client is None:
            raise LlmError(
                kind="not_configured",
                code="OPENAI_NOT_CONFIGURED",
                message="未配置 OPENAI_API_KEY",
            )
        kwargs: dict[str, Any] = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        try:
            resp = self._client.chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise _map_error(exc) from exc

        msg = resp.choices[0].message
        tool_calls: list[ToolCall] = []
        for tc in msg.tool_calls or []:
            try:
                arguments = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(
                ToolCall(name=tc.function.name, arguments=arguments, id=tc.id)
            )
        return ChatResult(content=msg.content, tool_calls=tool_calls)


def _map_error(exc: Exception) -> LlmError:
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return LlmError(kind="timeout", code="OPENAI_CALL_FAILED", message=str(exc))
    if isinstance(exc, RateLimitError):
        return LlmError(kind="rate_limit", code="OPENAI_RATE_LIMIT", message=str(exc))
    if isinstance(exc, BadRequestError):
        return LlmError(kind="bad_request", code="OPENAI_BAD_REQUEST", message=str(exc))
    return LlmError(kind="unknown", code="OPENAI_CALL_FAILED", message=str(exc))