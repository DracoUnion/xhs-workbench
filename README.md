# 自媒体 AI 工作台 · 桌面版（PySide6）

单进程 **PySide6 桌面应用**，源码按 src-layout 组织在 `src/` 下：
后端（SQLAlchemy + 任务编排 + 小红书 HTTP API 适配器）与前端同源，
PyQt 直接调用 `services` 层的服务函数，不再启动 HTTP/WebSocket 服务。

- 数据采集、Agent 任务编排（inline 线程）复用后端原实现；
- 小红书 xhs-cli 通过 **签名 HTTP API**（`src/adapters/xhs`）请求，不再依赖 Camoufox 浏览器；
- 后端尚未实现的接口（关键词/笔记/商品/账号/方向/Skill/内容包等）以**只读 SQL 视图**呈现，动作执行保留「待接入」。

## 运行

```bash
# 1. 安装后端依赖（首次，仓库根目录）
pip install -e .

# 2. 安装桌面 UI 依赖
pip install -r requirements.txt

# 3. 启动
python -m src        # 或 python src/main.py
```

启动后默认登录 `admin / admin123`。

> 桌面版使用**独立的数据库** `src/data/xhs_workbench.db`（与其他数据库隔离），
> 首次启动由后端 `init_db()` 自动建表与播种（管理员、5 个 Agent 定义、8 个榜单入口、风控参数）。

## 架构（均在 `src/` 下）

```
QApplication（主线程）
 ├─ main.py           — 入口：确保 src/ 在 sys.path → bootstrap → 建表播种 → QApplication
 ├─ main_window.py    — 侧边导航 + 顶栏 + QStackedWidget
 │    └─ gui/         — 页面（工作台/榜单/账号/商品/内容/任务中心/小红书/设置…）
 ├─ client.py         — 后端直连接口（独立 Session 调用 services，失败转 ApiError）
 ├─ ws_client.py      — 进程内事件桥（订阅后端进度广播 → Qt 信号）
 ├─ bootstrap.py      — 启动前置：src/data 独立数据库/日志路径/inline 执行器
 └─ adapters/xhs/     — 小红书签名 HTTP 客户端（httpx + xhshow 签名，终端 QR 登录）
```

关键文件：

| 文件（src/ 下） | 职责 |
|---|---|
| `main.py` | 入口：日志 → 建表播种 → QApplication → MainWindow |
| `bootstrap.py` | 在导入后端模块前设置环境（`src/data/` 独立数据库、`RUN_EXECUTOR=inline`） |
| `core/` | 配置、数据库引擎/Session、异常、日志、事件广播、安全 |
| `services/` | 领域服务：认证、Agent 运行编排、只读查询、评分、播种 |
| `models/` | ORM 模型注册表（discovery/production/content/orchestration/platform） |
| `adapters/` | LLM 适配器、小红书 xhs-cli HTTP 客户端（签到、重试、限速、QR 登录） |
| `agents/` | Agent 编排运行时（OpenAI Function Calling 循环） |
| `tools/` | 工具注册表（Agent 可调用的业务工具，含小红书采集） |
| `gui/` | PySide6 各页面（数据与操作与业务一一对应） |
| `widgets.py` | 共用 Qt 控件：表格、状态标签、详情块、审核/任务/消息对话框 |
| `styles.qss` | AntD 风格浅色主题 |

## 已实现 / 待接入

| 模块 | 功能 | 状态 |
|---|---|---|
| 登录 | 本地用户校验（bcrypt） + 内存会话 | ✅ 完整 |
| 任务中心 | 发起/列表/过滤/恢复/终止/消息/审核点 + 进程内事件实时刷新 | ✅ 完整（复用 services/runs） |
| 小红书 | 登录态查看、Cookie 保存/清除、HTTP 客户端采集工具、终端 QR 登录 | ✅ 完整（adapters/xhs） |
| 工作台 | 统计卡片 + 方向饼图 + 近期任务 | ✅ 只读视图 |
| 发现/制作/内容 | 榜单/账号/商品/方向/关键词/笔记/模板/Skill/内容包 | 🔶 只读视图，采集/评分/生成等动作「待接入」 |
| 设置 | Agent 定义、风控节奏 | 🔶 只读视图 |

## 说明

- 桌面版仅本机使用，不对外暴露任何端口。
- 若需启用 Agent 任务，设置 `OPENAI_API_KEY`（桌面版沿用 `.env`/环境变量配置）。