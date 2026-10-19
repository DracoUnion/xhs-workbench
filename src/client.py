"""后端直连客户端：PyQt 直接调用 app.services 的服务函数，替代原 HTTP 层。

- 每次调用在独立 SQLAlchemy Session 中执行，用后即关
- 后端异常（AppError）→ ApiError，保持与旧 HTTP 层一致的 code/message/details
- 登录态保存在 AuthStore；受保护操作基于当前用户做鉴权（替代原 JWT 依赖）
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.exceptions import AppError
from services import readonly
from services.auth import authenticate, issue_tokens
from services.runs import (
    abort_run,
    act_review_point,
    get_run,
    list_review_points,
    list_runs,
    resume_run,
    run_to_dict,
    submit_run,
)
from adapters.xhs import clear_cookies, cookie_status, set_cookie_string

TOKEN_INVALID_CODES = {"AUTH_REQUIRED", "TOKEN_INVALID", "PERMISSION_DENIED"}


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: Any = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code

    def __str__(self) -> str:  # pragma: no cover - 展示用
        return self.message


class AuthStore:
    """内存登录态：当前用户 + 兼容字段。清空时通过 on_auth_failed() 通知 UI 回登录页。"""

    def __init__(self) -> None:
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.user: dict[str, Any] | None = None
        self._listeners: list[Any] = []

    def add_listener(self, fn: Any) -> None:
        self._listeners.append(fn)

    def is_logged_in(self) -> bool:
        return bool(self.access_token and self.user)

    def clear(self) -> None:
        self.access_token = None
        self.refresh_token = None
        self.user = None
        for fn in self._listeners:
            fn()

    @property
    def username(self) -> str | None:
        return (self.user or {}).get("username")

    @property
    def role(self) -> str | None:
        return (self.user or {}).get("role")


class ApiClient:
    """PyQt → 后端服务的直连接口，方法签名与原 HTTP 客户端对齐（页面零改动）。"""

    def __init__(self, auth: AuthStore) -> None:
        self.auth = auth

    # ---------- 内部工具 ----------

    def _require_user(self) -> dict:
        user = self.auth.user
        if user is None:
            raise ApiError("AUTH_REQUIRED", "未登录")
        return user

    def _require_admin(self) -> dict:
        user = self._require_user()
        if user.get("role") != "admin":
            raise ApiError("PERMISSION_DENIED", "需要管理员权限")
        return user

    def _call(self, fn, *args: Any, **kwargs: Any) -> Any:
        """在独立 Session 中执行服务函数；AppError → ApiError。"""
        db: Session = SessionLocal()
        try:
            return fn(db, *args, **kwargs)
        except AppError as exc:
            if exc.code in TOKEN_INVALID_CODES and self.auth.is_logged_in():
                self.auth.clear()
            raise ApiError(exc.code, exc.message, exc.details) from exc
        finally:
            db.close()

    # ---------- 认证 ----------

    def login(self, username: str, password: str) -> dict:
        db: Session = SessionLocal()
        try:
            user = authenticate(db, username, password)
            tokens = issue_tokens(db, user)
            user_dict = {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
            }
        except AppError as exc:
            raise ApiError(exc.code, exc.message, exc.details) from exc
        finally:
            db.close()
        self.auth.access_token = tokens["access_token"]
        self.auth.refresh_token = tokens["refresh_token"]
        self.auth.user = user_dict
        return {"tokens": tokens, "user": user_dict}

    # ---------- 任务中心 ----------

    def list_tasks(
        self,
        status: str | None = None,
        agent_key: str | None = None,
        product_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list, dict]:
        self._require_user()
        items, total = self._call(
            list_runs,
            status=status,
            agent_key=agent_key,
            product_id=product_id,
            page=page,
            page_size=page_size,
        )
        return items, {"total": total, "page": page, "page_size": page_size}

    def get_task(self, run_id: int) -> dict:
        self._require_user()

        def _load(db: Session) -> dict:
            return run_to_dict(get_run(db, run_id))

        return self._call(_load)

    def get_task_messages(self, run_id: int) -> tuple[list, list]:
        self._require_user()

        def _load(db: Session) -> tuple[list, list]:
            run = get_run(db, run_id)
            return run.messages, run.tool_calls

        return self._call(_load)

    def create_task(self, agent_key: str, product_id: int | None = None, context: str | None = None) -> dict:
        self._require_user()
        return self._call(submit_run, agent_key, product_id=product_id, context=context)

    def resume_task(self, run_id: int) -> dict:
        self._require_user()
        mode = self._call(resume_run, run_id)
        return {"run_id": run_id, "mode": mode}

    def abort_task(self, run_id: int) -> dict:
        self._require_user()
        return self._call(abort_run, run_id)

    def list_review_points(self, pending_only: bool = True) -> list:
        self._require_user()
        return self._call(list_review_points, pending_only=pending_only)

    def act_review_point(self, point_id: int, action: str, note: str | None = None) -> dict:
        user = self._require_user()
        actor_id = int(user.get("id") or 0)
        return self._call(act_review_point, point_id, action, note, actor_id=actor_id)

    # ---------- 小红书 ----------

    def xhs_status(self) -> dict:
        self._require_user()
        return self._call(lambda db: cookie_status())

    def xhs_set_cookies(self, cookie: str) -> dict:
        self._require_admin()
        return self._call(lambda db: set_cookie_string(cookie))

    def xhs_clear_cookies(self) -> dict:
        self._require_admin()

        def _clear(db: Session) -> dict:
            cleared = clear_cookies()
            return {"cleared": cleared, "status": cookie_status()}

        return self._call(_clear)

    # ---------- 只读视图 ----------

    def dashboard_summary(self) -> dict:
        body = self._call(readonly.dashboard_summary)
        return body["data"]

    def ranking_sources(self) -> list:
        return self._call(readonly.ranking_sources)["data"]

    def list_accounts(self, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        body = self._call(readonly.list_accounts, page, page_size)
        return body["data"], body["meta"]

    def account_detail(self, account_id: int) -> dict | None:
        return self._call(readonly.account_detail, account_id)["data"]

    def list_products(
        self, *, account_id: int | None = None, role: str | None = None, page: int = 1, page_size: int = 50
    ) -> tuple[list, dict]:
        body = self._call(readonly.list_products, account_id, role, page, page_size)
        return body["data"], body["meta"]

    def product_detail(self, product_id: int) -> dict | None:
        return self._call(readonly.product_detail, product_id)["data"]

    def product_images(self, product_id: int) -> list:
        return self._call(readonly.product_images, product_id)["data"]

    def product_materials(self, product_id: int) -> list:
        return self._call(readonly.product_materials, product_id)["data"]

    def product_design(self, product_id: int) -> dict:
        return self._call(readonly.product_design, product_id)["data"]

    def list_directions(self) -> list:
        return self._call(readonly.list_directions)["data"]

    def list_keywords(self, product_id: int | None = None) -> list:
        return self._call(readonly.list_keywords, product_id)["data"]

    def list_notes(self, product_id: int | None = None, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        body = self._call(readonly.list_notes, product_id, page, page_size)
        return body["data"], body["meta"]

    def note_detail(self, note_id: int) -> dict | None:
        return self._call(readonly.note_detail, note_id)["data"]

    def note_analysis(self, note_id: int) -> dict:
        return self._call(readonly.note_analysis, note_id)["data"]

    def list_templates(self, product_id: int | None = None) -> list:
        return self._call(readonly.list_templates, product_id)["data"]

    def list_skills(self) -> list:
        return self._call(readonly.list_skills)["data"]

    def skill_detail(self, skill_id: int) -> dict | None:
        return self._call(readonly.skill_detail, skill_id)["data"]

    def list_contents(self, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        body = self._call(readonly.list_contents, page, page_size)
        return body["data"], body["meta"]

    def agent_defs(self) -> list:
        return self._call(readonly.agent_defs)["data"]

    def risk_config(self) -> list:
        return self._call(readonly.risk_config)["data"]


client: ApiClient | None = None
auth: AuthStore = AuthStore()


def get_client() -> ApiClient:
    global client
    if client is None:
        client = ApiClient(auth)
    return client