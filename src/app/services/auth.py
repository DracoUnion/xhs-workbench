"""认证领域服务：登录、签发/刷新令牌。"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AuthError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models import User


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username, User.is_active.is_(True)))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError(code="AUTH_FAILED", message="用户名或密码错误")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


def issue_tokens(db: Session, user: User) -> dict:
    s = get_settings()
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "expires_in": s.jwt_expire_seconds,
        "refresh_token": create_refresh_token(user.id),
    }


def refresh_access(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise AuthError(code="TOKEN_INVALID", message="刷新令牌无效或已过期")
    if payload.get("typ") != "refresh":
        raise AuthError(code="TOKEN_INVALID", message="非刷新令牌")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise AuthError(code="AUTH_REQUIRED", message="用户不存在或已停用")
    s = get_settings()
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "expires_in": s.jwt_expire_seconds,
        "refresh_token": create_refresh_token(user.id),
    }