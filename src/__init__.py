"""小红书 AI 工作台 · 桌面版（PySide6 + 后端直连）。

单进程 Qt 桌面应用：
- 后端包位于本目录 app/ 下（`import app` 由 bootstrap 的 sys.path 保证）
- PyQt 直接调用 app.services 的服务函数（进程内，无 HTTP 服务）
- 任务编排（inline 线程）复用后端原实现，运行事件经进程内广播转发为 Qt 信号
"""