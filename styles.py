"""AntD 风格浅色主题。"""
from __future__ import annotations

from pathlib import Path

QSS_FILE = Path(__file__).with_name("styles.qss")

QSS = QSS_FILE.read_text(encoding="utf-8")


def apply_styles(app) -> None:
    app.setStyleSheet(QSS)