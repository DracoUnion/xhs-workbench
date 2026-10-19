"""需求发现页面：榜单采集、账号画像(详情)、商品库(详情)、方向看板。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.widgets import (
    DataTable, DetailBlock, JsonViewer, Notice, Page,
    fmt_dt, fmt_json, fmt_money,
)


# ---------- 榜单采集 ----------


class RankingsPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "榜单采集", parent)
        toolbar = QHBoxLayout()
        subtitle = QLabel("千帆 8 个榜单入口 · 每页 60~90 秒随机延迟")
        subtitle.setObjectName("muted")
        toolbar.addWidget(subtitle)
        toolbar.addStretch()
        collect_btn = QPushButton("发起采集")
        collect_btn.setEnabled(False)
        collect_btn.setToolTip("待接入：浏览器采集尚未启动")
        toolbar.addWidget(collect_btn)
        self.root.insertLayout(1, toolbar)

        self.table = DataTable(
            [("Key", "key"), ("名称", "name"), ("页数上限", "page_max"), ("延迟", "delay_scope"), ("启用", "enabled")],
            self,
        )
        self.root.addWidget(self.table)
        self.root.addWidget(Notice("浏览器采集待接入，当前为只读视图"))
        self.root.addStretch()

    def refresh(self) -> None:
        rows = self.safe(self.client.ranking_sources)
        if rows is None:
            return
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "key": r.get("key"),
                    "name": r.get("name"),
                    "page_max": r.get("page_max"),
                    "delay_scope": r.get("delay_scope"),
                    "enabled": "是" if r.get("enabled") else "否",
                }
                for r in rows
            ]
        )


# ---------- 账号画像 ----------


class AccountsPage(Page):
    request_detail = Signal(str, dict)

    def __init__(self, client, parent=None):
        super().__init__(client, "账号画像", parent)
        self.table = DataTable(
            [("ID", "id"), ("昵称", "nickname"), ("粉丝", "fans"), ("评分", "score"),
             ("在榜天数", "board_days"), ("上榜类型", "board_types"), ("首次上榜", "first_seen_board")],
            self,
        )
        self.table.row_activated.connect(
            lambda row: self.request_detail.emit("discovery.account_detail", {"id": row.get("id")})
        )
        self.root.addWidget(self.table)
        self.root.addStretch()

    def refresh(self) -> None:
        result = self.safe(lambda: self.client.list_accounts(page=1, page_size=50))
        if result is None:
            return
        rows, meta = result
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": a.get("id"),
                    "nickname": a.get("nickname") or "—",
                    "fans": a.get("fans"),
                    "score": round(a["score"], 2) if isinstance(a.get("score"), (int, float)) else a.get("score"),
                    "board_days": a.get("board_days"),
                    "board_types": a.get("board_types"),
                    "first_seen_board": fmt_dt(a.get("first_seen_board")),
                }
                for a in rows
            ]
        )
        self.set_info(f"共 {meta.get('total', 0)} 个账号")


class AccountDetailPage(Page):
    go_back = Signal()

    def __init__(self, client, parent=None):
        super().__init__(client, "账号详情", parent)
        back = QPushButton("← 返回账号列表")
        back.clicked.connect(self.go_back.emit)
        self.root.insertWidget(1, back)
        self.detail = DetailBlock()
        self.root.addWidget(self.detail)
        metrics = QLabel("评分维度明细")
        metrics.setObjectName("cardTitle")
        self.root.addWidget(metrics)
        self.metrics_view = JsonViewer()
        self.root.addWidget(self.metrics_view)
        self.root.addWidget(Notice("账号分析与商品关联待接入，当前为只读视图"))
        self.root.addStretch()
        self._account_id: int | None = None

    def apply_context(self, params: dict) -> None:
        self._account_id = params.get("id")
        self.title_label.setText(f"账号详情 #{self._account_id}")

    def refresh(self) -> None:
        if not self._account_id:
            return
        data = self.safe(lambda: self.client.account_detail(self._account_id))
        if data is None:
            return
        self.clear_info()
        self.detail.clear()
        self.detail.add("昵称", data.get("nickname"))
        self.detail.add("小红书 ID", data.get("xhs_user_id"))
        self.detail.add("粉丝", f"{data.get('fans'):,}" if data.get("fans") else "—")
        score = data.get("score")
        self.detail.add("评分", round(score, 2) if isinstance(score, (int, float)) else score)
        self.detail.add("在榜天数", data.get("board_days"))
        self.detail.add("上榜类型", data.get("board_types"))
        self.detail.add("首次上榜", fmt_dt(data.get("first_seen_board")))
        metrics = (data.get("metrics") or {}).get("breakdown") or (data.get("metrics") or {})
        self.metrics_view.setPlainText(fmt_json(metrics))


# ---------- 商品库 ----------


class ProductsPage(Page):
    request_detail = Signal(str, dict)

    def __init__(self, client, parent=None):
        super().__init__(client, "商品库", parent)
        self.table = DataTable(
            [("ID", "id"), ("标题", "title"), ("价格", "price_cents"), ("销量", "sales"),
             ("形态", "form"), ("角色", "role"), ("状态", "status")],
            self,
        )
        self.table.row_activated.connect(
            lambda row: self.request_detail.emit("discovery.product_detail", {"id": row.get("id")})
        )
        self.root.addWidget(self.table)
        self.root.addStretch()

    def refresh(self) -> None:
        result = self.safe(lambda: self.client.list_products(page=1, page_size=50))
        if result is None:
            return
        rows, meta = result
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": p.get("id"),
                    "title": p.get("title") or "—",
                    "price_cents": fmt_money(p.get("price_cents")),
                    "sales": p.get("sales"),
                    "form": p.get("form") or "—",
                    "role": p.get("role") or "—",
                    "status": p.get("status") or "—",
                }
                for p in rows
            ]
        )
        self.set_info(f"共 {meta.get('total', 0)} 个商品")


class ProductDetailPage(Page):
    go_back = Signal()

    def __init__(self, client, parent=None):
        super().__init__(client, "商品详情", parent)
        back = QPushButton("← 返回商品库")
        back.clicked.connect(self.go_back.emit)
        self.root.insertWidget(1, back)
        self.detail = DetailBlock()
        self.root.addWidget(self.detail)
        imgs = QLabel("商品图片")
        imgs.setObjectName("cardTitle")
        self.root.addWidget(imgs)
        self.images = JsonViewer()
        self.root.addWidget(self.images)
        self.root.addStretch()
        self._product_id: int | None = None

    def apply_context(self, params: dict) -> None:
        self._product_id = params.get("id")
        self.title_label.setText(f"商品详情 #{self._product_id}")

    def refresh(self) -> None:
        if not self._product_id:
            return
        data = self.safe(lambda: self.client.product_detail(self._product_id))
        if data is None:
            return
        self.clear_info()
        self.detail.clear()
        self.detail.add("标题", data.get("title"))
        self.detail.add("小红书 ID", data.get("xhs_id"))
        self.detail.add("价格", fmt_money(data.get("price_cents")))
        self.detail.add("销量", data.get("sales"))
        self.detail.add("形态", data.get("form"))
        self.detail.add("角色", data.get("role"))
        self.detail.add("状态", data.get("status"))
        self.detail.add("分享链接", data.get("share_link"))
        self.images.setPlainText(fmt_json(
            [{"seq": i.get("seq"), "url": i.get("url"), "local_path": i.get("local_path")} for i in (data.get("images") or [])]
        ))


# ---------- 方向看板 ----------


class DirectionsPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "方向看板", parent)
        self.table = DataTable(
            [("ID", "id"), ("方向", "name"), ("品类", "category"), ("形态", "form"),
             ("状态", "status"), ("依据", "evidence"), ("选定商品", "picked_product_id")],
            self,
        )
        self.root.addWidget(self.table)
        self.root.addWidget(Notice("支撑账号/销量证据待接入，当前为只读视图"))
        self.root.addStretch()

    def refresh(self) -> None:
        rows = self.safe(self.client.list_directions)
        if rows is None:
            return
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "category": d.get("category") or "—",
                    "form": d.get("form") or "—",
                    "status": d.get("status"),
                    "evidence": (d.get("evidence") or "—")[:60],
                    "picked_product_id": d.get("picked_product_id"),
                }
                for d in rows
            ]
        )