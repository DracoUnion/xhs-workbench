"""小红书 AI 工作台 · 桌面版（PySide6 + 内嵌 FastAPI）。

单进程 Qt 桌面应用：
- 后端包位于本目录 app/ 下（`import app` 由 bootstrap 的 sys.path 保证）
- uvicorn 在进程内守护线程中监听 127.0.0.1:<随机端口>
- Qt 界面通过 HTTP + WebSocket 与该服务通信
- 业务逻辑、任务编排（inline 线程）、实时进度推送全部复用后端原实现
"""