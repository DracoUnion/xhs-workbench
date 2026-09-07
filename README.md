# 小红书 AI 工作台

小红书虚拟产品全自动运营系统（需求发现 → 产品制作 → 内容获客）。

文档：[PRD](./doc/prd.md) · [概要设计](./doc/概要设计文档.md) · [详细设计](./doc/详细设计文档.md)

## 技术栈

- 后端：FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL + Redis/Celery（OpenAI API 作 Agent 推理）
- 前端：React + Vite + TypeScript（规划中）

## 后端如何运行

```bash
# 1. 安装依赖（Python 3.10+）
pip install -r requirements.txt

# 2. 准备 PostgreSQL 16，并复制配置
cp .env.example .env          # 修改 DATABASE_URL / JWT_SECRET 等

# 3. 建库与初始迁移（首次）
alembic revision --autogenerate -m "init: platform orchestration discovery production content"
alembic upgrade head

# 4. 启动
python -m uvicorn app.main:app --reload --port 8000
# 或：xhs-backend
```

- 健康检查：`GET /healthz`
- 接口文档：`http://localhost:8000/docs`

数据库未就绪时后端也能启动（`/healthz` 可通），但登录等 DB 操作会报错——属预期。

## 初始账号

`ADMIN_USERNAME` / `ADMIN_PASSWORD`（默认 `admin` / `admin123`），首次启动自动播种。

## Agent / 任务中心（M0）

- **Agent 编排引擎**：`app/agents/runtime.py`（OpenAI Function Calling 循环）+ `app/tools/registry.py`（工具注册表）+ `app/adapters/llm/openai.py`（LLM Provider）。
- **评分服务**：`app/services/scoring.py`（PRD 4.1.3 纯函数，`pytest tests/test_scoring.py`）。
- **任务中心 API**：`GET/POST /api/v1/tasks`、`POST /tasks/{id}/resume|abort`、`PATCH /api/v1/review-points/{id}`。
- **实时进度**：`GET /ws/tasks?token=<jwt>`（WebSocket 推送 `run.progress/blocked/done/failed`）。
- **执行器**：`RUN_EXECUTOR=inline`（默认，无需 Redis）或 `celery`（需 Redis/Celery worker）。

首次跑任务前确保 `OPENAI_API_KEY` 已配置，并用 `alembic upgrade head` 建好表（Agent 定义由 seed 自动播种）。

## 小红书采集（xhs-cli 适配器）

`app/adapters/xhs/` 直接整合了 [jackwener/xhs-cli](https://github.com/jackwener/xhs-cli)（Apache-2.0）的浏览器采集客户端（读取 `__INITIAL_STATE__`，规避接口风控 300011）。

- **不装依赖也能启动**：浏览器依赖（camoufox）在函数内惰性导入，采集/登录不可用时抛 `XHS_BROWSER_UNAVAILABLE`，其余功能正常。
- **启用采集**：`pip install -e ".[xhs]"`。
- **登录态**：
  - 交互扫码：`python -m scripts.xhs_login`（宿主机终端跑，扫码后存 `~/.xhs-cli/cookies.json`）；
  - 或 API 下发 cookie：`PUT /api/v1/xhs/cookies`（admin，body `{cookie: "a1=...; web_session=..."}`）。
- **状态**：`GET /api/v1/xhs/status`。
- **工具**：`xhs_search_notes` / `xhs_get_note_detail` / `xhs_get_user_info` / `xhs_get_user_posts` / `xhs_get_note_comments`。

## 工程约定

- 核心错误体系见 `app.core.exceptions`，错误码 → HTTP 映射表在其末尾。
- 模型注册统一入口：`app.models`（Alembic 依赖 `Base.metadata`）。
- 目录职责：`core` 基础设施 · `models` ORM · `services` 业务 · `api/v1` 接口层 · `repositories` 仓储。