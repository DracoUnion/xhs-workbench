# 自媒体 AI 工作台 · 桌面版（PySide6）

单进程**桌面应用**：后端（FastAPI + SQLAlchemy + 任务编排 + 小红书适配器）整体位于本包
`src/app/`（保持 `import app` 命名，由 `bootstrap.py` 把 src/ 加入 sys.path 实现）；
原 React 前端已并入桌面端并移除。

- 后端以**内嵌 uvicorn** 方式运行在进程内守护线程（`127.0.0.1:<随机端口>`）；
- 客户端与后端交互，业务逻辑、任务编排（inline 线程）、实时进度 WebSocket 全部复用原实现；
- 后端尚未实现的接口（关键词/笔记/商品/账号/方向/Skill/内容包等）以**只读 SQL 视图**呈现，动作执行保留「待接入」。

## 运行

```bash
# 1. 安装后端依赖（首次，仓库根目录）
pip install -e .

# 2. 安装桌面 UI 依赖
pip install -r requirements.txt

# 3. 启动
python -m src
```

启动后默认登录 `admin / admin123`。

> 桌面版使用**独立的数据库** `src/data/xhs_workbench.db`（与其他数据库隔离），
> 首次启动由后端 `init_db()` 自动建表与播种（管理员、5 个 Agent 定义、8 个榜单入口、风控参数）。

## 架构

```
QApplication（主线程）
 ├─ MainWindow：侧边导航 + 顶栏 + QStackedWidget
 │    └─ pages/*.py       — 20 个页面（候选 Qt 组件）
 ├─ client.py             — httpx HTTP 客户端 + 内存登录态
 ├─ ws_client.py          — QThread WebSocket 客户端 → Qt 信号
 └─ server.py（守护线程）— uvicorn + app.main.create_app()（含只读路由）
      └─ readonly.py      — 只读 SQL 视图端点
```

关键文件：

| 文件 | 职责 |
|---|---|
| `bootstrap.py` | 在导入 `app.*` 前设置环境（独立数据库/日志路径/inline 执行器） |
| `server.py` | 查找空闲端口、重组 FastAPI 路由、启动/停止内嵌服务 |
| `readonly.py` | 只读端点：dashboard/summary、ranking-sources、accounts、products、directions、keywords、notes、templates、skills、contents、agent-defs、risk-config |
| `client.py` | `ApiClient`（封装 `{data:...}` 解包、`{error:...}` 抛 `ApiError`、Bearer 注入） |
| `ws_client.py` | `/ws/tasks` 任务事件客户端（指数退避重连） |
| `widgets.py` | 共用 Qt 控件：表格、状态标签、详情块、审核/任务/消息对话框 |
| `pages/*` | 各页面（数据与操作与 React 版一一对应） |
| `styles.qss` | AntD 风格浅色主题 |

## 已实现 / 待接入

| 模块 | 功能 | 状态 |
|---|---|---|
| 登录 | token 登录 + 当前用户 | ✅ 完整（内存会话） |
| 任务中心 | 发起/列表/过滤/恢复/终止/消息/审核点 + WS 实时进度 | ✅ 完整（复用后端 tasks/review-points） |
| 小红书 | 登录态查看、Cookie 保存/清除 | ✅ 完整（复用后端 xhs） |
| 工作台 | 统计卡片 + 方向饼图 + 近期任务 | ✅ 只读视图 |
| 发现/制作/内容 | 榜单/账号/商品/方向/关键词/笔记/模板/Skill/内容包 | 🔶 只读视图，采集/评分/生成等动作「待接入」 |
| 设置 | 执行器说明、Agent 定义、风控节奏 | 🔶 只读视图 |

## 说明

- 内嵌服务只监听 `127.0.0.1`，不对外网暴露。
- 关闭窗口时 `closeEvent` 会停止内嵌服务线程，进程干净退出。
- 若需对外提供 `OPENAI_API_KEY` 后使用 Agent 任务，设置同名环境变量即可（桌面版沿用 `.env`/环境变量配置）。