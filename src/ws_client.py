"""任务实时事件客户端：后台线程连接 /ws/tasks，通过 Qt 信号转发事件到 UI。

对齐 frontend/src/hooks/useTaskWebSocket.ts 的语义：
- 携带 access JWT（query token）
- 断线指数退避重连（1s*2^n，上限 30s）
- 收到 JSON 帧 → event_ready(dict)
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("src.ws")


class TaskEventClient(QThread):
    connected = Signal(bool)   # True=已连接 / False=断开
    event_ready = Signal(dict)  # 原始 {"type":..., "data":...}

    def __init__(self, auth: Any) -> None:
        super().__init__()
        self._auth = auth
        self._stop = threading.Event()
        self._max_backoff = 30.0

    def stop(self) -> None:
        self._stop.set()

    def _ws_url(self) -> str:
        from src.server import server_ws_url

        token = self._auth.access_token or ""
        return f"{server_ws_url()}?token={token}"

    def run(self) -> None:  # noqa: N802 - Qt 虚方法命名
        from websockets.sync.client import connect
        from websockets.exceptions import WebSocketException

        retries = 0
        while not self._stop.is_set():
            token = self._auth.access_token
            if not token:
                retries = 0
                self._stop.wait(1.0)
                continue

            try:
                with connect(self._ws_url(), close_timeout=3) as ws:
                    retries = 0
                    self.connected.emit(True)
                    for raw in ws:
                        if self._stop.is_set():
                            break
                        try:
                            event: dict = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            continue
                        self.event_ready.emit(event)
            except (WebSocketException, OSError, RuntimeError) as exc:
                logger.info("任务 WS 断开: %s", exc)
                self.connected.emit(False)
            except Exception as exc:  # noqa: BLE001 - 连接层杂项错误统一退避
                logger.info("任务 WS 异常: %s", exc)
                self.connected.emit(False)

            if self._stop.is_set():
                break
            delay = min(1.0 * (2 ** retries), self._max_backoff)
            retries += 1
            logger.info("任务 WS %ss 后重连", delay)
            self._stop.wait(delay)

        self.connected.emit(False)