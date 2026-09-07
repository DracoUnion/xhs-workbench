"""应用配置：环境变量与 .env 文件加载，映射为类型安全的设置对象。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。字段名大写时优先读同名环境变量（如 OPENAI_API_KEY）。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 启动 ----------
    app_name: str = "小红书 AI 工作台后端"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    # 任务执行器：inline（默认，无需 Redis）| celery（需 Redis/Celery worker）
    run_executor: str = "inline"

    # ---------- 数据库 ----------
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/xhs_workbench"

    # ---------- Redis / Celery ----------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None  # 缺省回退到 redis_url
    celery_result_backend: str | None = None

    # ---------- 鉴权 ----------
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_seconds: int = 7200          # access 2h
    jwt_refresh_expire_seconds: int = 1209600  # refresh 14d

    # ---------- LLM ----------
    openai_api_key: str = ""
    llm_model_default: str = "gpt-4o"

    # ---------- 小红书 xhs-cli 适配器 ----------
    xhs_cookie_file: str = "~/.xhs-cli/cookies.json"
    xhs_cookies: str = ""

    # ---------- 存储 ----------
    data_dir: str = "data"
    browser_contexts_dir: str = "data/browser-contexts"
    log_dir: str = "data/logs"

    # ---------- 设备 ----------
    adb_serial: str = ""
    adb_host: str = ""                      # 如 192.168.1.x:5555

    # ---------- 管理员（初始化用） ----------
    admin_username: str = "admin"
    admin_password: str = "admin123"

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()