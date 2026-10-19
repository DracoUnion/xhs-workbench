"""FastAPI 依赖：JWT 鉴权、当前用户、管理员。"""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthError, PermissionError
from app.core.security import decode_token
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """校验 Bearer access token 并返回当前用户；失败抛出 AuthError（由全局处理器转 401）。"""
    if creds is None:
        raise AuthError(code="AUTH_REQUIRED", message="未登录")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise AuthError(code="TOKEN_INVALID", message="凭证无效或已过期")
    if payload.get("typ") != "access":
        raise AuthError(code="TOKEN_INVALID", message="非访问令牌")
    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if user is None or not user.is_active:
        raise AuthError(code="AUTH_REQUIRED", message="用户不存在或已停用")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise PermissionError(code="PERMISSION_DENIED", message="需要管理员权限")
    return user