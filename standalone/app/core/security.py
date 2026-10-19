"""鉴权：bcrypt 密码哈希、JWT 签发与校验。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, expire_seconds: int, extra: dict[str, Any]) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=expire_seconds),
        "typ": extra.pop("typ", "access"),
        **extra,
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def create_access_token(user_id: int | str, role: str) -> str:
    return _create_token(str(user_id), get_settings().jwt_expire_seconds, {"role": role, "typ": "access"})


def create_refresh_token(user_id: int | str) -> str:
    return _create_token(str(user_id), get_settings().jwt_refresh_expire_seconds, {"typ": "refresh"})


def decode_token(token: str) -> dict[str, Any]:
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])


def token_kind(token: str) -> str:
    return decode_token(token).get("typ", "access")