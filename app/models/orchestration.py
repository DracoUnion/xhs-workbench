"""Orchestration 上下文：Agent 定义、执行 Run、审核点、去重记录。"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    UUID,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import PKMixin, TimestampMixin
from app.core.database import Base


class AgentDef(PKMixin, TimestampMixin, Base):
    """子 Agent 配置（提示词 + 工具白名单 + 模型），入库可在线改。"""

    __tablename__ = "agent_defs"

    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    tool_keys: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    model: Mapped[str] = mapped_column(String(48), nullable=False, server_default=text("'gpt-4o'"))
    temperature: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False, server_default=text("0.2"))
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("6 * 3600"))
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class AgentRun(PKMixin, TimestampMixin, Base):
    """一次 Agent 执行：全量上下文 JSONB 持久化 = 断点续跑能力。"""

    __tablename__ = "agent_runs"

    run_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, server_default=text("gen_random_uuid()")
    )
    agent_key: Mapped[str] = mapped_column(ForeignKey("agent_defs.key"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'")
    )  # pending|running|blocked|done|failed|killed
    messages: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    tool_calls: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    checkpoint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    continue_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 排队/复活时间

    __table_args__ = (
        Index("ix_agent_runs_status_continue", "status", "continue_at"),
        Index("ix_agent_runs_product", "product_id"),
    )


class ReviewPoint(PKMixin, Base):
    """检查点：AUTO / REVIEW / MANUAL；REVIEW 阻塞 Run 等人工动作。"""

    __tablename__ = "review_points"

    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"), nullable=False)
    agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    rtype: Mapped[str] = mapped_column(String(16), nullable=False)  # AUTO|REVIEW|MANUAL
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    action: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'pending'"))
    action_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_review_pending", "action", "rtype"),)


class Dedup(PKMixin, Base):
    """统一去重：同一产品下按 scope 去重（note|product|link）。"""

    __tablename__ = "dedup"

    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("uq_dedup_product_scope_fingerprint", "product_id", "scope", "fingerprint", unique=True),
    )