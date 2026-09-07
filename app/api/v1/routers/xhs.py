"""小红书登录态管理路由：查看状态、下发/清除 cookie。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adapters.xhs import clear_cookies, cookie_status, set_cookie_string
from app.api.v1.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models import User

router = APIRouter(prefix="/xhs", tags=["xhs"])


class SetCookiesBody(BaseModel):
    cookie: str = Field(..., description='cookie header 字符串，例如 "a1=...; web_session=..."')


@router.get("/status")
def status(_user: User = Depends(get_current_user)) -> dict:
    return {"data": cookie_status()}


@router.put("/cookies")
def set_cookies(
    body: SetCookiesBody,
    _admin: User = Depends(require_admin),
    _db: Session = Depends(get_db),
) -> dict:
    return {"data": set_cookie_string(body.cookie)}


@router.delete("/cookies")
def delete_cookies(_admin: User = Depends(require_admin)) -> dict:
    cleared = clear_cookies()
    return {"data": {"cleared": cleared, "status": cookie_status()}}