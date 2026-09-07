"""Agent 编排运行时：OpenAI Function Calling 循环，Store/Provider/Sink 注入，离线可测。"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.adapters.llm import LLMProvider
from app.core.exceptions import FatalError, LlmError, RecoverableError, ReviewRequired


# ---------- Agent 元信息 ----------


@dataclass
class AgentMeta:
    system_prompt: str
    model: str = "gpt-4o"
    temperature: float = 0.2
    tool_keys: list[str] = field(default_factory=list)


# ---------- 运行状态与存储抽象 ----------


@dataclass
class RunState:
    status: str = "pending"           # pending|running|blocked|done|failed|killed
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    checkpoint: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class RunStore(Protocol):
    """会话持久化端口；DB 实现见 services/runs.py，测试用 in-memory 实现。"""

    def load(self) -> RunState: ...
    def persist(self, state: RunState) -> None: ...
    def create_review_point(self, rtype: str, payload: Any) -> Any: ...


class EventSink(Protocol):
    def __call__(self, event: dict) -> None: ...


def parse_final(content: str | None) -> dict[str, Any]:
    """把模型最终回答解析为 result dict：合法 JSON 用之，否则包裹为 {'text': ...}。"""
    if not content:
        return {}
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else {"text": content}
    except json.JSONDecodeError:
        return {"text": content}


# ---------- 运行时 ----------


class AgentRuntime:
    def __init__(
        self,
        provider: LLMProvider,
        tools_registry: Any,
        store: RunStore,
        sink: EventSink | None = None,
        *,
        max_rounds: int = 60,
        max_attempts: int = 3,
        sleep_fn: Any = time.sleep,
    ) -> None:
        self.provider = provider
        self.tools_registry = tools_registry
        self.store = store
        self.sink = sink or (lambda _: None)
        self.max_rounds = max_rounds
        self.max_attempts = max_attempts
        self.sleep_fn = sleep_fn

    def _emit(self, event: dict) -> None:
        self.sink(event)

    def run(
        self, meta: AgentMeta, initial_messages: list[dict[str, Any]] | None = None
    ) -> RunState:
        state = self.store.load()
        # 幂等：终态或已阻塞的任务不做重入执行
        if state.status in ("done", "failed", "killed", "blocked"):
            return state
        state.status = "running"
        if initial_messages and not state.messages:
            state.messages = list(initial_messages)
        self.store.persist(state)

        for round_index in range(1, self.max_rounds + 1):
            conversation = [{"role": "system", "content": meta.system_prompt}, *state.messages]
            result = self._call_provider(meta, conversation, round_index, state)
            if isinstance(result, _Terminal):
                # _call_provider 已置 failed 并推送事件，直接返回
                return state
            round_start = len(state.messages)

            assistant_msg: dict[str, Any] = {"role": "assistant", "content": result.content}
            if result.tool_calls:
                assistant_msg["tool_calls"] = []
                for i, tc in enumerate(result.tool_calls):
                    call_id = tc.id or f"call_{round_index}_{i}"
                    assistant_msg["tool_calls"].append(
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                            },
                        }
                    )
            state.messages.append(assistant_msg)

            if not result.tool_calls:
                state.status = "done"
                state.result = parse_final(result.content)
                state.checkpoint = None
                self.store.persist(state)
                self._emit({"type": "run.done", "data": {"result": state.result}})
                return state

            for i, tc in enumerate(result.tool_calls):
                call_id = tc.id or f"call_{round_index}_{i}"
                try:
                    ok, out = self.tools_registry.invoke(tc.name, tc.arguments)
                except ReviewRequired as rq:
                    # 回滚本轮，保证 resume 后消息流一致
                    del state.messages[round_start:]
                    state.status = "blocked"
                    point_id = self.store.create_review_point(
                        rtype=rq.rtype, payload=rq.payload
                    )
                    self.store.persist(state)
                    self._emit(
                        {
                            "type": "run.blocked",
                            "data": {
                                "point_id": point_id,
                                "rtype": rq.rtype,
                                "payload": rq.payload,
                                "tool": tc.name,
                            },
                        }
                    )
                    return state
                except FatalError as fe:
                    del state.messages[round_start:]
                    state.status = "failed"
                    state.error = {"code": fe.code, "message": fe.message}
                    self.store.persist(state)
                    self._emit({"type": "run.failed", "data": {"error": state.error}})
                    return state
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tc.name,
                    "content": json.dumps(out, ensure_ascii=False),
                }
                state.messages.append(tool_msg)
                state.tool_calls.append(
                    {"name": tc.name, "arguments": tc.arguments, "ok": ok}
                )
                self._emit(
                    {"type": "run.progress", "data": {"tool": tc.name, "ok": ok}}
                )

            self.store.persist(state)

        # 达到 max_rounds 仍未收敛，视为失败
        state.status = "failed"
        state.error = {"code": "AGENT_MAX_ROUNDS", "message": f"超过 {self.max_rounds} 轮未收敛"}
        self.store.persist(state)
        self._emit({"type": "run.failed", "data": {"error": state.error}})
        return state

    def _call_provider(
        self,
        meta: AgentMeta,
        conversation: list[dict[str, Any]],
        round_index: int,
        state: RunState,
    ):
        tools = self.tools_registry.tools_for(meta.tool_keys)
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self.provider.chat(
                    conversation,
                    tools=tools or None,
                    model=meta.model,
                    temperature=meta.temperature,
                )
            except RecoverableError as exc:
                last_error = exc
            except LlmError as exc:
                if exc.kind == "not_configured":
                    state.status = "failed"
                    state.error = {"code": exc.code, "message": exc.message}
                    self.store.persist(state)
                    self._emit({"type": "run.failed", "data": {"error": state.error}})
                    return _Terminal(exc)
                last_error = exc
            if attempt < self.max_attempts:
                self.sleep_fn(min(2**attempt, 8))
        state.status = "failed"
        state.error = {"code": "OPENAI_CALL_FAILED", "message": str(last_error)}
        self.store.persist(state)
        self._emit({"type": "run.failed", "data": {"error": state.error}})
        return _Terminal(last_error)


class _Terminal:
    """Provider 失败导致终止的哨兵，避免继续进入工具处理。"""

    def __init__(self, exc: Exception | None = None) -> None:
        self.exc = exc
        self.content = None
        self.tool_calls = []