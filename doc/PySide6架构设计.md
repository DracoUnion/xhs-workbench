# xhs-workbench 架构设计

> 自媒体 AI 工作台（PySide6 + SQLAlchemy + Agent 运行时）。本文件描述架构对齐后的当前代码结构（2026-10-30），
> 补充 `doc/prd.md`、`doc/概要设计文档.md`、`doc/详细设计文档.md` 中未覆盖的架构层。

## 1. 项目简介

小红书自媒体运营工作台：内容发现、生产、物料管理、Agent 编排（OpenAI function calling）、
小红书平台适配（登录/签名/cookies/HTTP）、评分、任务中心。桌面版以进程内 SQLite + inline 执行
替代原 HTTP/Web 后端；`src/` 布局 + Alembic 迁移 + 可选 Celery/Postgres。

变更历史：`4d71830` 新增零 Qt 架构层（common/tasks/bootstrap），`main.py` 装配 AppContext 并关闭任务池。

## 2. 技术栈与依赖（根 `pyproject.toml` + `requirements.txt`）

| 项 | 值 |
|---|---|
| Qt 绑定 | PySide6 ≥ 6.6（桌面 requirements） |
| DB/ORM | SQLAlchemy 2 + Alembic（默认 SQLite，可切 psycopg/Postgres） |
| 认证/安全 | JWT + bcrypt + pycryptodome（XHS 签名） |
| 任务 | celery（可选）+ inline daemon Thread（桌面强制 `RUN_EXECUTOR=inline`） |
| LLM | openai + httpx + agents/tools registry |
| 平台适配 | adapters/xhs（client/bridge/auth/cookies/signing/html_parser） |
| 测试 | pytest（scoring / tools / xhs adapter 离线 + 架构层） |

## 3. 目录结构

```text
xhs-workbench/
├─ pyproject.toml + requirements.txt + conftest.py + alembic/ + alembic.ini
├─ src/
│  ├─ __main__.py / main.py     # 入口：bootstrap env → init_db → auto-login → MainWindow
│  ├─ bootstrap.py              # env 副作用（DATA_DIR/DATABASE_URL/RUN_EXECUTOR）+ build_context()
│  ├─ common/                   # ★ 零 Qt（本次新增）
│  │  ├─ events.py              # EventHub（UI 事件适配；业务用 core.events.EventBus）
│  │  ├─ context.py             # AppContext
│  │  └─ __init__.py
│  ├─ tasks/                    # ★ 零 Qt
│  │  ├─ task.py                # Task/TaskState/TaskManager（通用，本次新增）
│  │  ├─ celery_app.py / runs.py# Celery + inline run 调度（业务运行权威路径）
│  │  └─ __init__.py
│  ├─ core/                     # config/database/events(EventBus)/logging/security/ws_manager
│  ├─ models/                   # content/discovery/mixins/orchestration/platform/production
│  ├─ services/                 # auth/readonly/runs/scoring/seed
│  ├─ agents/                   # runtime + prompts（AgentRuntime，Store/Provider/Sink）
│  ├─ tools/                    # registry + implementations + xhs_tools
│  ├─ adapters/                 # llm/openai + xhs/*
│  ├─ client.py                 # ApiClient（进程内直连 services，保留 HTTP 接口形状）
│  ├─ ws_client.py              # 订阅 ws_manager sink → Qt signal（非真 WebSocket）
│  ├─ main_window.py            # 侧栏 QListWidget + QStackedWidget
│  ├─ gui/                      # dashboard/discovery/production/content/settings/task_center/xhs 页面
│  ├─ widgets.py / theme.py / styles.py / styles.qss
│  └─ data/                     # xhs_workbench.db + logs（gitignored）
└─ tests/                       # test_scoring / test_tools / test_xhs_adapter / test_arch
```

## 4. 架构分层与依赖方向

```text
gui/ + main_window.py (唯一 PySide6)
 └─ client.py  ApiClient（HTTP 形状兼容层，进程内直连 services）
     └─ services / models / adapters / agents / tools
         └─ core/（database/events/security/logging）+ tasks/
             └─ common/（EventHub / AppContext）
```

`adapters/` 即参考架构的 `clients/` 外层（外部依赖：LLM、XHS 平台）。`core.events.EventBus`
（Pydantic DomainEvent）是业务事件总线；`common.events.EventHub` 是 UI 侧任务事件适配。

## 5. 关键流程

```text
python -m src 或 console script xhs-workbench
→ src/main.py run()
   ├─ import bootstrap        # env 副作用：DATA_DIR/DATABASE_URL=sqlite/RUN_EXECUTOR=inline
   ├─ setup_logging()
   ├─ init_db()（Alembic head）
   ├─ _auto_login()（get_client().login(admin) → AuthStore）
   ├─ ctx = build_context()   # Settings + EventHub + TaskManager → AppContext
   ├─ QApplication + apply_styles → MainWindow()（win.ctx = ctx）
   └─ app.exec() → ctx.tasks.shutdown(wait=False)
```

Agent 运行：`services.runs` 每 run daemon Thread，独立 SQLAlchemy Session，状态机
`pending/running/blocked/done/failed/killed`，支持 checkpoint/review point/事件 sink；
可切 Celery（`tasks/celery_app.py`），桌面 bootstrap 强制 inline。

## 6. 线程模型

| 线程 | 职责 |
|---|---|
| Qt 主线程 | 窗口 / 页面 / 短查询 |
| daemon Thread（services.runs） | Agent run 执行（inline），独享 Session |
| Q 事件桥（ws_client → Qt signal） | 订阅 ws_manager sink 推送页面 |
| TaskManager 池（零 Qt） | 通用后台任务（AppContext.tasks，为 UI 桥预留） |
| Celery（可选） | 非桌面部署的分布式执行 |

## 7. 配置管理

- `.env` + pydantic-settings（`core/config.py`：DATABASE_URL、admin_username/password、
  XHS cookies/QR、Redis/Celery 可选）。
- 桌面强制 `DATABASE_URL=sqlite:///src/data/xhs_workbench.db` + `RUN_EXECUTOR=inline`（bootstrap）。
- 业务数据：SQLite/Postgres + Alembic 迁移；日志 `src/data/logs`。
- 无 QSettings 桌面偏好（可后续补 `ui/settings_store.py`）。

## 8. 测试

```bash
# 后端（离线）：scoring / tools registry / xhs adapter（需 pycryptodome 'Crypto'）
./.venv/Scripts/python.exe -m pytest tests -q
# 架构层：tests/test_arch.py（EventHub/TaskManager/bootstrap）
```

## 9. 与参考架构的差距（后续 TODO）

- 无独立 `schemas/` 目录（服务直接返回 dict），可加 Pydantic DTO。
- `client.py` 是模块级 `get_client()` 全局客户端、无 `ServiceFacade` 类——可用 facade 组合按域服务。
- `adapters/` 可改名/别名 `clients/` 对齐参考架构命名。
- 无 `ui/settings_store.py`（QSettings 偏好）；`scripts/` 尚无正式打包 spec（PyInstaller/Nuitka）。