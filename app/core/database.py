"""数据库引擎与会话：SQLAlchemy 2.0 风格，Alembic 共用该 metadata。"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

# naming_convention：让 Alembic 迁移能自动为约束生成稳定名称，便于回滚与复用
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    # 数据库未启动时快速失败，避免启动流程被连接超时阻塞
    # connect_args={"connect_timeout": 3},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求一个 Session，用完即关。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()