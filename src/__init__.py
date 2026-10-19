"""自媒体 AI 工作台 · 桌面版（PySide6 + 后端直连）。

单进程 Qt 桌面应用：
- 后端子包（core/services/models/adapters/...）位于本目录下，由 bootstrap 加入 sys.path
- PyQt 直接调用 services 等后端服务函数（进程内，无 HTTP 服务）
- 任务编排（inline 线程）复用后端原实现，运行事件经进程内广播转发为 Qt 信号
"""