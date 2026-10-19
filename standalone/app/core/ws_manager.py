"""WebSocket 连接管理：把运行事件推送给前端任务中心。单机设计，进程内广播。"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop | None) -> None:
        """在应用启动时绑定主事件循环，供跨线程 broadcast_sync 派发。"""
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        for ws in list(self.active):
            try:
                await ws.send_json(event)
            except Exception:  # noqa: BLE001  单条连接失败不影响其余
                self.active.discard(ws)

    def broadcast_sync(self, event: dict[str, Any]) -> None:
        """给行工作线程（Celery/inline）用的同步派发；未绑定主循环时静默丢弃。"""
        loop = self._loop
        if loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(self.broadcast(event), loop)
        except RuntimeError:  # loop 已关闭
            pass


ws_manager = ConnectionManager()