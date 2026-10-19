# 小红书 AI 工作台（桌面版）

小红书虚拟产品全自动运营系统（需求发现 → 产品制作 → 内容获客）。单进程 **PySide6 桌面应用**，
后端（FastAPI）内嵌于进程内守护线程。

文档：[PRD](./doc/prd.md) · 概要设计 · 详细设计

## 目录结构

```
app/                （已并入 standalone/app/）
standalone/
  main.py / __main__.py   # 桌面应用入口 python -m standalone
  app/                    # 后端包（FastAPI + SQLAlchemy + 任务编排 + 小红书适配器）
  pages/                  # PySide6 页面
  readonly.py             # 只读 SQL 视图端点
  client.py               # HTTP 客户端 + 登录态
  ws_client.py            # 任务事件 WebSocket 客户端
  server.py               # 内嵌 uvicorn + 只读路由组装
  bootstrap.py            # 环境准备（独立数据库/日志路径，sys.path）
  styles.qss              # AntD 风格浅色主题
  data/                   # 运行时生成：xhs_workbench.db、日志（gitignore）
frontend/            # React 前端已并入桌面端，目录已删除
tests/               # 后端 pytest（conftest.py 使 `import app` 解析到 standalone/app）
```

## 技术栈

- 桌面：PySide6（Qt6）· QtCharts
- 后端：FastAPI · SQLAlchemy 2 · SQLite（内嵌于桌面进程）
- 任务编排：OpenAI Function Calling · inline 线程执行 · WebSocket 实时进度
- 小红书采集：xhs-cli（Camoufox 浏览器适配，可选安装）

## 运行

```bash
# 1. 安装依赖（Python 3.10+，仓库根目录）
pip install -e .
pip install -r standalone/requirements.txt

# 2. 启动桌面应用
python -m standalone
# 初始账号：admin / admin123（standalone/data/xhs_workbench.db 首次启动自动建库播种）
```

## 功能边界

| 模块 | 状态 |
|---|---|
| 登录、任务中心（发起/恢复/终止/消息/审核点 + 实时进度） | ✅ 完整 |
| 小红书登录态（Cookie 查看/保存/清除） | ✅ 完整 |
| 工作台、榜单/账号/商品/方向/关键词/笔记/模板/Skill/内容包 | 🔶 只读视图（采集/评分/生成等动作「待接入」） |
| 设置 | 🔶 只读视图 |

## 说明

- 内嵌服务只监听 `127.0.0.1:<随机端口>`，不对外网暴露。
- 桌面版使用独立数据库 `standalone/data/xhs_workbench.db`。
- Agent 任务需要 `OPENAI_API_KEY`（环境变量或 `.env`）。
- 后端测试：`python -m pytest tests/ -q`。
- 交互式小红书扫码登录：`python -m scripts.xhs_login`（需 `pip install -e ".[xhs]"`）。