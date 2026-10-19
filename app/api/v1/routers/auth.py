"""认证路由：登录、刷新、当前用户。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.schemas import LoginRequest, RefreshRequest, TokenResponse, UserOut
from app.core.database import get_db
from app.models import User
from app.services.auth import authenticate, issue_tokens, refresh_access

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db, body.username, body.password)
    return TokenResponse(**issue_tokens(db, user))


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return TokenResponse(**refresh_access(db, body.refresh_token))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user