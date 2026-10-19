"""桌面版入口：初始化环境 → 初始化后端 → 显示主窗口。"""
from __future__ import annotations

import sys

# 必须先设置环境再导入任何 app.*（见 bootstrap 文档说明）。
import bootstrap  # noqa: F401
from app.core.logging import get_logger, setup_logging
from app.services.seed import init_db

logger = get_logger("src.main")


def run() -> None:
    # 替代原内嵌 HTTP 服务：PyQt 直接调用 services 层（app/main.startup_backend）。
    setup_logging()
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001 - 数据库不可用时不阻断启动
        logger.warning("database unavailable at startup; continue booting", error=str(exc))

    from PySide6.QtWidgets import QApplication

    from main_window import MainWindow
    from styles import apply_styles

    app = QApplication(sys.argv)
    app.setApplicationName("小红书 AI 工作台")
    apply_styles(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()