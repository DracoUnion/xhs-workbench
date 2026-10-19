"""内嵌 FastAPI 服务：守护线程中运行 uvicorn，Qt 界面通过 HTTP/WebSocket 访问。

关键点：必须先 import src.bootstrap（已由 __main__ 或 main 完成）。
readonly_router 将在 create_app() 之前并入 app.api.v1.router.api_router，
这样 create_app() 复制路由时即包含只读视图，且落在末尾 catch-all 404 之前，
避免被 Starlette 的顺序匹配遮蔽。
"""
from __future__ import annotations

import logging
import socket
import threading
from typing import Any

import uvicorn

import src.readonly  # noqa: F401  (模块级引入以复用其 router 对象)
from app.api.v1.router import api_router
from src.readonly import router as readonly_router

logger = logging.getLogger("src.server")

# 启动后填充：Qt 界面 client.py 读取该端口。
SERVER_HOST = "127.0.0.1"
SERVER_PORT: int | None = None

_server: uvicorn.Server | None = None
_thread: threading.Thread | None = None


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((SERVER_HOST, 0))
        return int(sock.getsockname()[1])

def build_app(port: int) -> Any:
    """构造 FastAPI app：扩展聚合路由后再交给 app.main.create_app()。"""
    # 将只读视图并入后端聚合路由（在 create_app 复制路由之前），
    # 保证 /api/v1/* 的只读端点不被主应用末尾的 catch-all 404 遮蔽。
    api_router.include_router(readonly_router)

    # create_app() 内部已 include api_router（含 readonly）与 ws_router。
    from app.main import create_app

    app = create_app()

    # 便于客户端探活：/healthz 已存在；补充返回绑定端口信息。
    @app.get("/src/info", include_in_schema=False)
    def _info() -> dict:
        return {"status": "ok", "host": SERVER_HOST, "port": port}

    return app


def start_server() -> int:
    """启动内嵌服务（守护线程），返回监听端口。调用前必须先跑 src.bootstrap。"""
    global SERVER_PORT, _server, _thread
    SERVER_PORT = _find_free_port()
    app = build_app(SERVER_PORT)
    config = uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT, log_level="warning")
    _server = uvicorn.Server(config)

    def _run() -> None:
        _server.run()  # 阻塞；lifespan 会绑定 WS 主循环并 init_db() 播种

    _thread = threading.Thread(target=_run, name="src-uvicorn", daemon=True)
    _thread.start()

    # 等待服务真正就绪（lifespan 完成后 started 置 True）
    import time  # noqa: PLC0415 - 局部导入，避免影响 import 顺序
    for _ in range(200):
        if getattr(_server, "started", False):
            break
        time.sleep(0.05)

    if not getattr(_server, "started", False):
        raise RuntimeError("内嵌服务未能在预期时间内启动")
    logger.info("内嵌服务已启动: http://%s:%s", SERVER_HOST, SERVER_PORT)
    return SERVER_PORT


def stop_server() -> None:
    """请求服务优雅退出；守护线程随之结束，进程可退出。"""
    global _server
    if _server is not None:
        _server.should_exit = True
        _server = None
    logger.info("内嵌服务已请求退出")


def server_base_url() -> str:
    assert SERVER_PORT is not None, "内嵌服务尚未启动"
    return f"http://{SERVER_HOST}:{SERVER_PORT}"


def server_ws_url() -> str:
    assert SERVER_PORT is not None, "内嵌服务尚未启动"
    return f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/tasks"