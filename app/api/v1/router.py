"""API v1 聚合路由：后续模块在此挂载。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers import auth

api_router = APIRouter()
api_router.include_router(auth.router)
# 后续：dashboard / rankings / accounts / products / directions /
#       keywords / notes / templates / skills / contents / tasks / reviews / settings