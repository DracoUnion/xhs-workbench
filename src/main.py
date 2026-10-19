"""桌面版入口：初始化环境 → 启动内嵌服务 → 显示主窗口。"""
from __future__ import annotations

import sys

# 必须先设置环境再导入任何 app.*（见 bootstrap 文档说明）。
import bootstrap  # noqa: F401


def run() -> None:
    import server as srv
    from PySide6.QtWidgets import QApplication

    from main_window import MainWindow
    from styles import apply_styles

    srv.start_server()

    app = QApplication(sys.argv)
    app.setApplicationName("小红书 AI 工作台")
    apply_styles(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
