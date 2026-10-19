"""FastAPI 应用工厂：生命周期、异常处理器、路由挂载。"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.api.v1.ws import ws_router
from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.exceptions import AppError, HTTP_STATUS_BY_CODE
from app.core.logging import get_logger, setup_logging
from app.core.ws_manager import ws_manager
from app.services.seed import init_db
from app.models import init_tables

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # 绑定主事件循环，供 Celery/inline 工作线程同步推送 WS 事件
    ws_manager.bind_loop(asyncio.get_running_loop())
    # 数据库不可用时（如尚未启动/建表）不阻断进程，便于先启动看健康检查
    try:
        init_db()
        logger.info("database initialized")
    except Exception as exc:  # noqa: BLE001
        logger.warning("database unavailable at startup; continue booting", error=str(exc))
    yield
    ws_manager.bind_loop(None)
    engine.dispose()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, lifespan=lifespan, debug=s.debug)

    # ---- 统一异常响应格式：{"error": {"code", "message", "details"}} ----

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_STATUS_BY_CODE.get(exc.code, 400),
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "请求参数校验失败",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": None,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "服务器内部错误",
                    "details": str(exc),
                }
            },
        )

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict:
        return {"status": "ok", "app": s.app_name, "debug": s.debug}

    app.include_router(api_router, prefix=s.api_v1_prefix)
    app.include_router(ws_router)  # /ws/tasks 不进 /api/v1 前缀

    # 兜底 404：统一格式
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def catch_all_404(request: Request, path: str):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"路径不存在: {request.url.path}",
                    "details": None,
                }
            },
        )

    return app


app = create_app()


def run() -> None:  # pragma: no cover - 本地启动入口
    import uvicorn
    init_db()
    s = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=s.debug)


if __name__ == "__main__":
    run()