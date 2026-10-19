"""LLM 适配层的稳定接口。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    id: str | None = None


@dataclass(frozen=True)
class ChatResult:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(Protocol):
    def chat(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> ChatResult: ...


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """返回进程级 Provider；真正的 OpenAI client 延迟到此处初始化。"""
    global _provider
    if _provider is None:
        from app.adapters.llm.openai import OpenAIProvider

        _provider = OpenAIProvider()
    return _provider


__all__ = ["ChatResult", "ToolCall", "LLMProvider", "get_llm_provider"]