"""主窗口：侧边导航 + 顶栏 + 页面堆栈。对齐 frontend/src/layouts/MainLayout.tsx。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QStackedWidget, QVBoxLayout, QWidget,
)

from client import get_client
from gui.content import (
    ContentsPage, KeywordsPage, NoteDetailPage, NotesPage, SkillEditorPage,
    SkillsPage, TemplatesPage,
)
from gui.dashboard import DashboardPage
from gui.discovery import (
    AccountDetailPage, AccountsPage, DirectionsPage, ProductDetailPage,
    ProductsPage, RankingsPage,
)
from gui.production import ProductStudioPage, ProductionProductsPage
from gui.settings import SettingsPage
from gui.task_center import TaskCenterPage
from gui.xhs import XhsPage
from ws_client import TaskEventClient

# (导航项文本, 路由 key)
NAV_ITEMS: list[tuple[str, str]] = [
    ("工作台", "dashboard"),
    ("榜单采集", "rankings"),
    ("账号画像", "accounts"),
    ("商品库", "products"),
    ("方向看板", "directions"),
    ("产品列表", "production_products"),
    ("关键词", "keywords"),
    ("对标笔记库", "notes"),
    ("模板聚类", "templates"),
    ("内容 Skill", "skills"),
    ("内容包", "contents"),
    ("任务中心", "tasks"),
    ("小红书", "xhs"),
    ("设置", "settings"),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("自媒体 AI 工作台")
        self.resize(1280, 820)
        self.client = get_client()

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)
        self.setCentralWidget(self._body)

        # 进程内事件桥
        self.ws = TaskEventClient(self.client.auth)
        self.ws.event_ready.connect(self._on_ws_event)
        self.ws.connected.connect(self._on_ws_connected)
        self.ws.start()

        # 启动直接进入主界面（登录态由 main.py 在启动时建立）
        self._build_app()
        self._body_layout.addWidget(self._app_widget)
        self._app_widget.show()
        self.ws.connected.emit(True)

    # ---------- 主界面 ----------

    def _build_app(self) -> None:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 侧边导航
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 12, 0, 12)
        logo = QLabel("自媒体 AI 工作台")
        logo.setObjectName("logo")
        side.addWidget(logo)

        self.nav = QListWidget()
        self.nav.setObjectName("navList")
        for text, key in NAV_ITEMS:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, key)
            self.nav.addItem(item)
        self.nav.currentItemChanged.connect(self._on_nav)
        side.addWidget(self.nav, 1)
        layout.addWidget(sidebar, 1)

        # 右侧内容区
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 8, 24, 8)
        self.ws_badge = QLabel("● 实时连接中")
        self.ws_badge.setObjectName("wsBadge")
        header.addWidget(self.ws_badge)
        header.addStretch()
        user_box = QHBoxLayout()
        self.user_label = QLabel()
        self.user_label.setObjectName("userLabel")
        user_box.addWidget(self.user_label)
        header.addLayout(user_box)
        header_frame = QFrame()
        header_frame.setObjectName("headerBar")
        header_frame.setLayout(header)
        right.addWidget(header_frame)

        self.stack = QStackedWidget()
        pages: dict[str, QWidget] = {}
        self._detail_stack: dict[str, QWidget] = {}

        # —— 顶层页面 ——
        dashboard = DashboardPage(self.client)
        pages["dashboard"] = dashboard

        rankings = RankingsPage(self.client)
        pages["rankings"] = rankings

        accounts = AccountsPage(self.client)
        accounts.request_detail.connect(self._open_detail)
        pages["accounts"] = accounts

        products = ProductsPage(self.client)
        products.request_detail.connect(self._open_detail)
        pages["products"] = products

        directions = DirectionsPage(self.client)
        pages["directions"] = directions

        production_products = ProductionProductsPage(self.client)
        production_products.request_detail.connect(self._open_detail)
        pages["production_products"] = production_products

        keywords = KeywordsPage(self.client)
        pages["keywords"] = keywords

        notes = NotesPage(self.client)
        notes.request_detail.connect(self._open_detail)
        pages["notes"] = notes

        templates = TemplatesPage(self.client)
        pages["templates"] = templates

        skills = SkillsPage(self.client)
        skills.request_detail.connect(self._open_detail)
        pages["skills"] = skills

        contents = ContentsPage(self.client)
        pages["contents"] = contents

        self.task_center = TaskCenterPage(self.client)
        pages["tasks"] = self.task_center

        xhs = XhsPage(self.client)
        pages["xhs"] = xhs

        settings = SettingsPage(self.client)
        pages["settings"] = settings

        # —— 详情页（非导航直达）——
        account_detail = AccountDetailPage(self.client)
        account_detail.go_back.connect(lambda: self._back_to("accounts"))
        self._detail_stack["account_detail"] = account_detail

        product_detail = ProductDetailPage(self.client)
        product_detail.go_back.connect(lambda: self._back_to("products"))
        self._detail_stack["product_detail"] = product_detail

        product_studio = ProductStudioPage(self.client)
        product_studio.go_back.connect(lambda: self._back_to("production_products"))
        self._detail_stack["product_studio"] = product_studio

        note_detail = NoteDetailPage(self.client)
        note_detail.go_back.connect(lambda: self._back_to("notes"))
        self._detail_stack["note_detail"] = note_detail

        skill_editor = SkillEditorPage(self.client)
        skill_editor.go_back.connect(lambda: self._back_to("skills"))
        self._detail_stack["skill_editor"] = skill_editor

        for key, page in pages.items():
            self.stack.addWidget(page)
            page.setObjectName(key)
        for key, page in self._detail_stack.items():
            self.stack.addWidget(page)
            page.setObjectName(key)

        right.addWidget(self.stack, 1)
        layout.addLayout(right, 5)

        self.pages = pages
        self._app_widget = widget
        self._current_route: str | None = None

        self.user_label.setText(self.client.auth.username or "")
        self._nav_to("dashboard")

    def _nav_to(self, key: str) -> None:
        self._current_route = key
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        page.refresh()

    def _on_nav(self, current: QListWidgetItem | None) -> None:
        if current is None:
            return
        self._nav_to(current.data(Qt.UserRole))

    # ---------- 详情页导航 ----------

    def _open_detail(self, route: str, params: dict) -> None:
        page = self._detail_stack.get(route)
        if page is None:
            return
        page.apply_context(params)
        self.stack.setCurrentWidget(page)
        page.refresh()
        # 记录来源以便返回
        self._detail_back: tuple[str, dict] = (route, params)

    def _back_to(self, parent_key: str) -> None:
        self._nav_to(parent_key)

    # ---------- WS ----------

    def _on_ws_event(self, event: dict) -> None:
        if self.task_center is not None:
            self.task_center.on_event(event)
        # Dashboard 近期任务随事件刷新（对齐 react-query version 失效）
        if self._current_route == "dashboard":
            self.pages["dashboard"].refresh()

    def _on_ws_connected(self, ok: bool) -> None:
        if ok:
            self.ws_badge.setText("● 实时连接中")
        else:
            self.ws_badge.setText("○ 未连接")

    # ---------- 关闭 ----------

    def closeEvent(self, event) -> None:  # noqa: N802
        self.ws.stop()
        self.ws.wait(3000)
        super().closeEvent(event)
