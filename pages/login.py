"""登录页：对齐 frontend/src/pages/Login。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from standalone.client import ApiError


class LoginPage(QWidget):
    logged_in = Signal()

    def __init__(self, client, auth, parent=None):
        super().__init__(parent)
        self.client = client
        self.auth = auth
        outer = QHBoxLayout(self)
        outer.addStretch()
        center = QVBoxLayout()
        center.setSpacing(12)
        outer.addLayout(center, 3)
        outer.addStretch()

        logo = QLabel("小红书 AI 工作台")
        logo.setObjectName("loginLogo")
        logo.setAlignment(Qt.AlignCenter)
        center.addWidget(logo)

        sub = QLabel("需求发现 → 产品制作 → 内容获客")
        sub.setObjectName("muted")
        sub.setAlignment(Qt.AlignCenter)
        center.addWidget(sub)

        self.username = QLineEdit("admin")
        self.username.setPlaceholderText("用户名")
        self.password = QLineEdit("admin123")
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.Password)
        center.addWidget(self.username)
        center.addWidget(self.password)

        self.error = QLabel()
        self.error.setObjectName("errorText")
        self.error.setAlignment(Qt.AlignCenter)
        self.error.hide()
        center.addWidget(self.error)

        self.login_btn = QPushButton("登 录")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.clicked.connect(self._submit)
        center.addWidget(self.login_btn)

        hint = QLabel("初始账号 admin / admin123（在 standalone/data 独立数据库播种）")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)
        center.addWidget(hint)

        self.username.returnPressed.connect(self._submit)
        self.password.returnPressed.connect(self._submit)

    def _submit(self) -> None:
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self._show_error("请输入用户名和密码")
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中…")
        try:
            self.client.login(username, password)
        except ApiError as exc:
            self._show_error(exc.message)
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登 录")
            return
        except Exception as exc:  # noqa: BLE001
            self._show_error(f"登录失败：{exc}")
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登 录")
            return
        self.error.hide()
        self.logged_in.emit()

    def _show_error(self, text: str) -> None:
        self.error.setText(text)
        self.error.show()
