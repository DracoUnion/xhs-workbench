"""小红书登录态：对齐 frontend/src/pages/Xhs。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QWidget,
)

from src.client import ApiError
from src.widgets import ConfirmDialog, DetailBlock, Page, StatCard


class XhsPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "小红书登录态", parent)

        top = QHBoxLayout()
        self.auth_stat = StatCard("登录态", "未知", "#1677ff")
        top.addWidget(self.auth_stat)
        top.addWidget(QLabel("要求 cookie：a1 + web_session；来源：XHS_COOKIES 或 ~/.xhs-cli/cookies.json"))
        top.addStretch()
        self.root.addLayout(top)

        status_box = QVBoxLayout()
        title = QLabel("当前状态")
        title.setObjectName("cardTitle")
        status_box.addWidget(title)
        self.detail = DetailBlock()
        status_box.addWidget(self.detail)
        self.root.addLayout(status_box)

        cookie_box = QVBoxLayout()
        title2 = QLabel("配置 Cookie")
        title2.setObjectName("cardTitle")
        cookie_box.addWidget(title2)
        self.cookie_edit = QTextEdit()
        self.cookie_edit.setPlaceholderText('粘贴 cookie header 字符串，例如 "a1=...; web_session=..."')
        self.cookie_edit.setFixedHeight(90)
        cookie_box.addWidget(self.cookie_edit)
        btn_row = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        clear_btn = QPushButton("清除登录态")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        cookie_box.addLayout(btn_row)
        self.root.addLayout(cookie_box)

        self.root.addStretch()
        self.refresh()

    def refresh(self) -> None:
        status = self.safe(self.client.xhs_status)
        if status is None:
            return
        self.clear_info()
        ok = bool(status.get("authenticated"))
        self.auth_stat.set_value("已登录" if ok else "未登录")
        self.auth_stat.value.setStyleSheet(f"color:{'#389e0d' if ok else '#cf1322'};")
        self.detail.clear()
        self.detail.add("认证状态", "已登录" if ok else "未登录")
        self.detail.add("必需字段", ", ".join(status.get("required", [])))
        self.detail.add("已就绪字段", ", ".join(status.get("present", [])) or "（无）")
        self.detail.add("Cookie 文件", status.get("cookie_file"))
        self.detail.add("来源", status.get("source"))

    def _save(self) -> None:
        cookie = self.cookie_edit.toPlainText().strip()
        if not cookie:
            self.set_info("请输入 cookie", True)
            return
        result = self.safe(lambda: self.client.xhs_set_cookies(cookie))
        if result:
            self.set_info("Cookie 已保存")
            self.cookie_edit.clear()
            self.refresh()

    def _clear(self) -> None:
        dialog = ConfirmDialog("确定清除小红书登录态？", self)
        if dialog.exec() != dialog.Accepted:
            return
        result = self.safe(self.client.xhs_clear_cookies)
        if result is not None:
            self.set_info("登录态已清除")
            self.refresh()
