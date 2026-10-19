"""进程内事件广播：把运行事件分发给已注册的 sink（Qt 界面等）。

替代原 WebSocket 连接管理。单机桌面应用不再需要 HTTP/WS 传输，
广播同步执行；sink 侧（ws_client.py）负责跨线程投递为 Qt 信号。
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class ConnectionManager:
    """向所有已注册 sink 同步派发运行事件。线程安全。"""

    def __init__(self) -> None:
        self._sinks: list[Callable[[dict[str, Any]], None]] = []
        self._lock = threading.Lock()

    def add_sink(self, sink: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(sink)

    def remove_sink(self, sink: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)

    def broadcast_sync(self, event: dict[str, Any]) -> None:
        """供 inline/Celery 工作线程同步派发；单个 sink 失败不影响其余。"""
        with self._lock:
            sinks = list(self._sinks)
        for sink in sinks:
            try:
                sink(event)
            except Exception:  # noqa: BLE001
                pass


ws_manager = ConnectionManager()
