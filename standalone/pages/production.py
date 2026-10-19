"""产品制作页面：产品列表（自产）、产品工作室。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from standalone.widgets import (
    DataTable, DetailBlock, JsonViewer, Notice, Page, fmt_dt, fmt_json, fmt_money,
)

DESIGN_STAGES = ["requirements", "prototype", "ui", "logic", "accept"]
DESIGN_LABELS = {"requirements": "需求", "prototype": "原型", "ui": "界面", "logic": "逻辑", "accept": "验收"}


class ProductionProductsPage(Page):
    request_detail = Signal(str, dict)

    def __init__(self, client, parent=None):
        super().__init__(client, "产品列表", parent)
        self.table = DataTable(
            [("ID", "id"), ("标题", "title"), ("价格", "price_cents"), ("销量", "sales"),
             ("形态", "form"), ("角色", "role"), ("状态", "status")],
            self,
        )
        self.table.row_activated.connect(
            lambda row: self.request_detail.emit("production.product_studio", {"id": row.get("id")})
        )
        self.root.addWidget(self.table)
        toolbar = QHBoxLayout()
        promote_btn = QPushButton("转自产")
        promote_btn.setEnabled(False)
        promote_btn.setToolTip("待接入：PATCH /products/{id} 尚未实现")
        toolbar.addWidget(promote_btn)
        toolbar.addStretch()
        self.root.insertLayout(1, toolbar)
        self.root.addWidget(Notice("仅展示自产（self-made）产品；「转自产」待接入"))
        self.root.addStretch()

    def refresh(self) -> None:
        result = self.safe(lambda: self.client.list_products(role="self-made", page=1, page_size=50))
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
        self.set_info(f"共 {meta.get('total', 0)} 个自产产品")


class ProductStudioPage(Page):
    go_back = Signal()

    def __init__(self, client, parent=None):
        super().__init__(client, "产品工作室", parent)
        back = QPushButton("← 返回产品列表")
        back.clicked.connect(self.go_back.emit)
        self.root.insertWidget(1, back)

        stage_title = QLabel("开发阶段")
        stage_title.setObjectName("cardTitle")
        self.root.addWidget(stage_title)
        self.stage_bar = QLabel()
        self.stage_bar.setObjectName("stageBar")
        self.root.addWidget(self.stage_bar)

        material_title = QLabel("资料清单")
        material_title.setObjectName("cardTitle")
        self.root.addWidget(material_title)
        self.materials = DataTable(
            [("ID", "id"), ("文件名", "filename"), ("类型", "mime"), ("大小", "size_bytes"), ("解析", "ingest_status")],
            self,
        )
        self.root.addWidget(self.materials)

        design_title = QLabel("开发配置")
        design_title.setObjectName("cardTitle")
        self.root.addWidget(design_title)
        self.design = DetailBlock()
        self.root.addWidget(self.design)
        self.root.addWidget(Notice("资料上传/验收报告待接入，当前为只读视图"))
        self.root.addStretch()
        self._product_id: int | None = None

    def apply_context(self, params: dict) -> None:
        self._product_id = params.get("id")
        self.title_label.setText(f"产品工作室 #{self._product_id}")

    def refresh(self) -> None:
        if not self._product_id:
            return
        self.clear_info()

        material_rows = self.safe(lambda: self.client.product_materials(self._product_id))
        if material_rows is not None:
            self.materials.set_rows(
                [
                    {
                        "id": m.get("id"),
                        "filename": m.get("filename") or "—",
                        "mime": m.get("mime") or "—",
                        "size_bytes": m.get("size_bytes"),
                        "ingest_status": m.get("ingest_status") or "—",
                    }
                    for m in material_rows
                ]
            )

        design = self.safe(lambda: self.client.product_design(self._product_id))
        if design:
            stage = design.get("stage", "")
            idx = DESIGN_STAGES.index(stage) if stage in DESIGN_STAGES else -1
            bars = []
            for i, s in enumerate(DESIGN_STAGES):
                label = DESIGN_LABELS.get(s, s)
                if i < idx:
                    bars.append(f"[✓] {label}")
                elif i == idx:
                    bars.append(f"[●] {label}")
                else:
                    bars.append(f"[ ] {label}")
            self.stage_bar.setText("  →  ".join(bars))
            self.design.clear()
            self.design.add("阶段", DESIGN_LABELS.get(stage, stage))
            self.design.add("仓库", design.get("repo_url"))
            self.design.add("构建路径", design.get("build_path"))
        else:
            self.stage_bar.setText("尚无开发阶段记录")