"""HTTP 客户端：对齐 frontend/src/api/http.ts 的 axios 层。

- 统一透传 Bearer token（来自 AuthStore）
- 错误响应 {"error":{code,message,details}} → 抛 ApiError
- 响应 {"data":...} 自动解包；分页接口额外返回 meta
- 服务不可用（连接被拒）→ 抛 CONNECTION_ERROR
"""
from __future__ import annotations

import json
from typing import Any

import httpx

import standalone.server as server

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
    """内存会话：tokens + 当前用户。token 过期时通过 on_auth_failed() 通知 UI 回登录页。"""

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
    def __init__(self, auth: AuthStore) -> None:
        self.auth = auth
        self._http: httpx.Client | None = None
        self._timeout = 30.0

    def _client(self) -> httpx.Client:
        if self._http is None:
            base = server.server_base_url() + "/api/v1"
            self._http = httpx.Client(base_url=base, timeout=self._timeout)
        return self._http

    def _headers(self) -> dict[str, str]:
        if self.auth.access_token:
            return {"Authorization": f"Bearer {self.auth.access_token}"}
        return {}

    def _handle_auth_failure(self, code: str) -> None:
        if code in TOKEN_INVALID_CODES and self.auth.is_logged_in():
            self.auth.clear()

    def request(self, method: str, path: str, *, params: dict | None = None, json_body: Any = None) -> dict:
        """发请求；错误信封 → 抛 ApiError；有 data 则解包，否则原样返回 body。"""
        headers = self._headers()
        try:
            resp = self._client().request(method, path, params=params, json=json_body, headers=headers)
        except httpx.TransportError as exc:
            raise ApiError("CONNECTION_ERROR", f"无法连接内嵌服务：{exc}")
        body: dict = {}
        if resp.content:
            try:
                body = resp.json()
            except json.JSONDecodeError:
                body = {}
        if isinstance(body, dict) and "error" in body:
            err = body["error"]
            code = (err or {}).get("code", "HTTP_ERROR")
            self._handle_auth_failure(code)
            raise ApiError(code, (err or {}).get("message", resp.text), (err or {}).get("details"), resp.status_code)
        if not resp.is_success and isinstance(body, dict) and "data" not in body:
            self._handle_auth_failure("HTTP_ERROR")
            raise ApiError(f"HTTP_{resp.status_code}", resp.text or f"请求失败 ({resp.status_code})", None, resp.status_code)
        return body.get("data", body) if isinstance(body, dict) else {}

    def request_page(self, method: str, path: str, *, params: dict | None = None, json_body: Any = None) -> dict:
        """分页接口：返回 {data, meta} 原始 body。"""
        headers = self._headers()
        try:
            resp = self._client().request(method, path, params=params, json=json_body, headers=headers)
        except httpx.TransportError as exc:
            raise ApiError("CONNECTION_ERROR", f"无法连接内嵌服务：{exc}")
        body: dict = {}
        if resp.content:
            try:
                body = resp.json()
            except json.JSONDecodeError:
                body = {}
        if isinstance(body, dict) and "error" in body:
            err = body["error"]
            code = (err or {}).get("code", "HTTP_ERROR")
            self._handle_auth_failure(code)
            raise ApiError(code, (err or {}).get("message", resp.text), (err or {}).get("details"), resp.status_code)
        return body

    def get(self, path: str, params: dict | None = None):
        return self.request("GET", path, params=params)

    def get_page(self, path: str, params: dict | None = None) -> tuple[list, dict]:
        body = self.request_page("GET", path, params=params)
        return body.get("data", []), body.get("meta", {})

    def post(self, path: str, body: Any = None):
        return self.request("POST", path, json_body=body)

    def put(self, path: str, body: Any = None):
        return self.request("PUT", path, json_body=body)

    def patch(self, path: str, body: Any = None):
        return self.request("PATCH", path, json_body=body)

    def delete(self, path: str):
        return self.request("DELETE", path)

    # ---------- 认证 ----------

    def login(self, username: str, password: str) -> dict:
        body = self.post("/auth/login", {"username": username, "password": password})
        self.auth.access_token = body["access_token"]
        self.auth.refresh_token = body.get("refresh_token")
        user = self.request("GET", "/auth/me")
        self.auth.user = user
        return {"tokens": body, "user": user}

    # ---------- 任务中心 ----------

    def list_tasks(
        self,
        status: str | None = None,
        agent_key: str | None = None,
        product_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list, dict]:
        params: dict = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if agent_key:
            params["agent_key"] = agent_key
        if product_id is not None:
            params["product_id"] = product_id
        return self.get_page("/tasks", params)

    def get_task(self, run_id: int) -> dict:
        return self.get(f"/tasks/{run_id}")

    def get_task_messages(self, run_id: int) -> tuple[list, list]:
        # 该端点响应为 {"data": messages, "tool_calls": [...]}（非标准平衡信封），用 request_page 保留两个字段。
        body = self.request_page("GET", f"/tasks/{run_id}/messages")
        return body.get("data", []), body.get("tool_calls", [])

    def create_task(self, agent_key: str, product_id: int | None = None, context: str | None = None) -> dict:
        body: dict = {"agent_key": agent_key}
        if product_id is not None:
            body["product_id"] = product_id
        if context:
            body["context"] = context
        return self.post("/tasks", body)

    def resume_task(self, run_id: int) -> dict:
        return self.post(f"/tasks/{run_id}/resume")

    def abort_task(self, run_id: int) -> dict:
        return self.post(f"/tasks/{run_id}/abort")

    def list_review_points(self, pending_only: bool = True) -> list:
        return self.get("/review-points", {"pending_only": "true" if pending_only else "false"})

    def act_review_point(self, point_id: int, action: str, note: str | None = None) -> dict:
        body: dict = {"action": action}
        if note:
            body["note"] = note
        return self.patch(f"/review-points/{point_id}", body)

    # ---------- 小红书 ----------

    def xhs_status(self) -> dict:
        return self.get("/xhs/status")

    def xhs_set_cookies(self, cookie: str) -> dict:
        return self.put("/xhs/cookies", {"cookie": cookie})

    def xhs_clear_cookies(self) -> dict:
        return self.delete("/xhs/cookies")

    # ---------- 只读视图 ----------

    def dashboard_summary(self) -> dict:
        return self.get("/dashboard/summary")

    def ranking_sources(self) -> list:
        return self.get("/ranking-sources")

    def list_accounts(self, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        return self.get_page("/accounts", {"page": page, "page_size": page_size})

    def account_detail(self, account_id: int) -> dict | None:
        return self.get(f"/accounts/{account_id}")

    def list_products(self, *, account_id: int | None = None, role: str | None = None, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        params: dict = {"page": page, "page_size": page_size}
        if account_id is not None:
            params["account_id"] = account_id
        if role:
            params["role"] = role
        return self.get_page("/products", params)

    def product_detail(self, product_id: int) -> dict | None:
        return self.get(f"/products/{product_id}")

    def product_images(self, product_id: int) -> list:
        return self.get(f"/products/{product_id}/images")

    def product_materials(self, product_id: int) -> list:
        return self.get(f"/products/{product_id}/materials")

    def product_design(self, product_id: int) -> dict:
        return self.get(f"/products/{product_id}/design")

    def list_directions(self) -> list:
        return self.get("/directions")

    def list_keywords(self, product_id: int | None = None) -> list:
        params = {"product_id": product_id} if product_id is not None else None
        return self.get("/keywords", params)

    def list_notes(self, product_id: int | None = None, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        params: dict = {"page": page, "page_size": page_size}
        if product_id is not None:
            params["product_id"] = product_id
        return self.get_page("/notes", params)

    def note_detail(self, note_id: int) -> dict | None:
        return self.get(f"/notes/{note_id}")

    def note_analysis(self, note_id: int) -> dict:
        return self.get(f"/notes/{note_id}/analysis")

    def list_templates(self, product_id: int | None = None) -> list:
        params = {"product_id": product_id} if product_id is not None else None
        return self.get("/templates", params)

    def list_skills(self) -> list:
        return self.get("/skills")

    def skill_detail(self, skill_id: int) -> dict | None:
        return self.get(f"/skills/{skill_id}")

    def list_contents(self, page: int = 1, page_size: int = 50) -> tuple[list, dict]:
        return self.get_page("/contents", {"page": page, "page_size": page_size})

    def agent_defs(self) -> list:
        return self.get("/agent-defs")

    def risk_config(self) -> list:
        return self.get("/risk-config")


client: ApiClient | None = None
auth: AuthStore = AuthStore()


def get_client() -> ApiClient:
    global client
    if client is None:
        client = ApiClient(auth)
    return client