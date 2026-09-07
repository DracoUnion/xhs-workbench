"""WebSocket 路由：/ws/tasks 实时任务进度推送。"""
from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.ws_manager import ws_manager

ws_router = APIRouter()


@ws_router.websocket("/ws/tasks")
async def ws_tasks(websocket: WebSocket, token: str = Query(...)) -> None:
    """鉴权：query token 必须是有效 access JWT；否则 1008 拒绝。"""
    try:
        payload = decode_token(token)
    except Exception:  # noqa: BLE001
        await websocket.close(code=1008)
        return
    if payload.get("typ") != "access":
        await websocket.close(code=1008)
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            # 预留：接收前端控制指令（心跳等）；目前仅维持连接
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)