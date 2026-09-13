"""Platform 上下文：用户、风控配置、应用配置。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import TimestampMixin
from app.core.database import Base


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'operator'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username} ({self.role})>"


class RiskConfig(Base):
    """风控节奏配置：每个动作 scope 的随机延迟区间与重试参数。"""

    __tablename__ = "risk_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    min_delay_s: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("60"))
    max_delay_s: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("90"))
    retry_max: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("3"))
    backoff_exp: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("2"))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class AppSetting(Base):
    """应用级键值配置（如 locators、llm.model_default），value 为 JSON。"""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )