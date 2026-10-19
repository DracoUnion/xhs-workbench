"""进程内事件总线：初版单机实现，预留替换为 Redis Pub/Sub / 消息队列的接口。"""
from __future__ import annotations

from collections.abc import Callable

import pydantic


class DomainEvent(pydantic.BaseModel):
    """领域事件基础；子类（如 ProductVerified）由各自服务定义。"""

    event_type: str


class EventBus:
    """发布/订阅总线。Handler 签名：(event) -> None。"""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[DomainEvent], None]]] = {}

    def register(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.event_type, []):
            handler(event)


# 模块级单例，跨服务共享
_bus = EventBus()


def get_bus() -> EventBus:
    return _bus