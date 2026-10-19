"""任务实时事件桥：订阅进程内广播并转发为 Qt 信号。

桌面版不再连接 WebSocket。后端运行线程调用 ws_manager.broadcast_sync，
本对象将事件转成 Qt 信号，沿用原页面的 connected/event_ready 接口。
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal

from core.ws_manager import ws_manager


class TaskEventClient(QObject):
    connected = Signal(bool)
    event_ready = Signal(dict)

    def __init__(self, auth: Any = None) -> None:
        super().__init__()
        # 保留旧构造参数，桌面直连模式不再读取 token。
        self._auth = auth
        self._subscribed = False

    def start(self) -> None:
        """注册进程内事件 sink；保留旧 QThread.start() 调用语义。

        connected 信号由界面自行驱动（进入主界面/登出），此处不主动置位，
        避免在主界面构建完成前触发无关 UI 更新。
        """
        if self._subscribed:
            return
        ws_manager.add_sink(self._on_event)
        self._subscribed = True

    def _on_event(self, event: dict) -> None:
        # 广播可能来自 inline worker；Qt 自动将跨线程连接排队到 GUI 线程。
        self.event_ready.emit(event)

    def stop(self) -> None:
        if self._subscribed:
            ws_manager.remove_sink(self._on_event)
            self._subscribed = False
        self.connected.emit(False)

    def wait(self, _msecs: int) -> bool:
        """兼容旧 QThread.wait()；直连 sink 无需等待后台线程。"""
        return True
