"""内容获客页面：关键词、对标笔记库(详情)、模板聚类、Skill、内容包。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, QVBoxLayout,
)

from src.widgets import (
    DataTable, DetailBlock, JsonViewer, Notice, Page, fmt_dt, fmt_json,
)


# ---------- 关键词 ----------


class KeywordsPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "关键词", parent)
        toolbar = QHBoxLayout()
        collect_btn = QPushButton("发起采集")
        collect_btn.setEnabled(False)
        collect_btn.setToolTip("待接入：关键词采集依赖未实现的业务接口")
        toolbar.addWidget(collect_btn)
        toolbar.addStretch()
        self.root.insertLayout(1, toolbar)

        self.table = DataTable(
            [("ID", "id"), ("产品", "product_id"), ("关键词", "word"), ("核心", "is_core"),
             ("A-Z", "a_to_z"), ("采集评论", "collect_comments"), ("目标页数", "pages_target"), ("已采集", "collected_count")],
            self,
        )
        self.root.addWidget(self.table)
        self.root.addWidget(Notice("关键词新增与采集待接入，当前为只读视图"))
        self.root.addStretch()

    def refresh(self) -> None:
        rows = self.safe(self.client.list_keywords)
        if rows is None:
            return
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": k.get("id"),
                    "product_id": k.get("product_id"),
                    "word": k.get("word"),
                    "is_core": "是" if k.get("is_core") else "否",
                    "a_to_z": "是" if k.get("a_to_z") else "否",
                    "collect_comments": "是" if k.get("collect_comments") else "否",
                    "pages_target": k.get("pages_target"),
                    "collected_count": k.get("collected_count"),
                }
                for k in rows
            ]
        )


# ---------- 对标笔记库 ----------


class NotesPage(Page):
    request_detail = Signal(str, dict)

    def __init__(self, client, parent=None):
        super().__init__(client, "对标笔记库", parent)
        self.table = DataTable(
            [("ID", "id"), ("标题", "title"), ("作者", "author"), ("类型", "media_type"),
             ("互动(赞/藏/评)", "interactions"), ("已拆解", "analyzed"), ("采集时间", "collected_at")],
            self,
        )
        self.table.row_activated.connect(
            lambda row: self.request_detail.emit("content.note_detail", {"id": row.get("id")})
        )
        self.root.addWidget(self.table)
        self.root.addStretch()

    def refresh(self) -> None:
        result = self.safe(lambda: self.client.list_notes(page=1, page_size=50))
        if result is None:
            return
        rows, meta = result
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": n.get("id"),
                    "title": n.get("title") or "—",
                    "author": n.get("author") or "—",
                    "media_type": n.get("media_type") or "—",
                    "interactions": f"{i.get('likes', 0)}/{i.get('collects', 0)}/{i.get('comments', 0)}"
                    if (i := n.get("interactions")) else "—",
                    "analyzed": "是" if n.get("analyzed") else "否",
                    "collected_at": fmt_dt(n.get("collected_at")),
                }
                for n in rows
            ]
        )
        self.set_info(f"共 {meta.get('total', 0)} 篇")

    def set_rows(self, rows):
        self.table.set_rows(rows)


class NoteDetailPage(Page):
    go_back = Signal()

    def __init__(self, client, parent=None):
        super().__init__(client, "笔记详情", parent)
        back = QPushButton("← 返回笔记库")
        back.clicked.connect(self.go_back.emit)
        self.root.insertWidget(1, back)
        self.detail = DetailBlock()
        self.root.addWidget(self.detail)

        body_title = QLabel("正文")
        body_title.setObjectName("cardTitle")
        self.root.addWidget(body_title)
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        self.body.setMaximumHeight(140)
        self.root.addWidget(self.body)

        analysis_title = QLabel("单篇拆解")
        analysis_title.setObjectName("cardTitle")
        self.root.addWidget(analysis_title)
        self.title_formula = QLabel()
        self.title_formula.setWordWrap(True)
        self.root.addWidget(self.title_formula)
        self.analysis_view = JsonViewer()
        self.root.addWidget(self.analysis_view)
        self.root.addStretch()
        self._note_id: int | None = None

    def apply_context(self, params: dict) -> None:
        self._note_id = params.get("id")
        self.title_label.setText(f"笔记详情 #{self._note_id}")

    def refresh(self) -> None:
        if not self._note_id:
            return
        data = self.safe(lambda: self.client.note_detail(self._note_id))
        if data is None:
            return
        self.clear_info()
        self.detail.clear()
        self.detail.add("标题", data.get("title"))
        self.detail.add("作者", data.get("author"))
        self.detail.add("笔记 ID", data.get("note_id"))
        self.detail.add("类型", data.get("media_type"))
        self.detail.add("A-Z 分组", data.get("a_to_z_group"))
        self.detail.add("已拆解", "是" if data.get("analyzed") else "否")
        self.body.setPlainText(data.get("body") or "")
        analysis = self.safe(lambda: self.client.note_analysis(self._note_id))
        if analysis:
            self.title_formula.setText(analysis.get("title_formula") or "")
            self.analysis_view.setPlainText(fmt_json(analysis))


# ---------- 模板聚类 ----------


class TemplatesPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "模板聚类", parent)
        self.table = DataTable(
            [("ID", "id"), ("产品", "product_id"), ("聚类键", "cluster_key"), ("支撑笔记", "supported_count"),
             ("状态", "status"), ("草稿", "draft_md")],
            self,
        )
        self.root.addWidget(self.table)
        self.root.addWidget(Notice("「转 Skill」待接入（需 3 篇以上支撑且业务接口就绪）"))
        self.root.addStretch()

    def refresh(self) -> None:
        rows = self.safe(self.client.list_templates)
        if rows is None:
            return
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": t.get("id"),
                    "product_id": t.get("product_id"),
                    "cluster_key": t.get("cluster_key"),
                    "supported_count": t.get("supported_count"),
                    "status": t.get("status"),
                    "draft_md": (t.get("draft_md") or "")[:60],
                }
                for t in rows
            ]
        )


# ---------- Skill ----------


class SkillsPage(Page):
    request_detail = Signal(str, dict)

    def __init__(self, client, parent=None):
        super().__init__(client, "内容 Skill", parent)
        self.table = DataTable(
            [("ID", "id"), ("名称", "name"), ("产品", "product_id"), ("状态", "status"),
             ("审查策略", "review_policy"), ("版本", "current_version")],
            self,
        )
        self.table.row_activated.connect(
            lambda row: self.request_detail.emit("content.skill_editor", {"id": row.get("id")})
        )
        self.root.addWidget(self.table)
        self.root.addStretch()

    def refresh(self) -> None:
        rows = self.safe(self.client.list_skills)
        if rows is None:
            return
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "product_id": s.get("product_id"),
                    "status": s.get("status"),
                    "review_policy": s.get("review_policy"),
                    "current_version": s.get("current_version"),
                }
                for s in rows
            ]
        )


class SkillEditorPage(Page):
    go_back = Signal()

    def __init__(self, client, parent=None):
        super().__init__(client, "Skill 编辑", parent)
        back = QPushButton("← 返回 Skill 列表")
        back.clicked.connect(self.go_back.emit)
        self.root.insertWidget(1, back)
        self.meta = QLabel()
        self.meta.setObjectName("muted")
        self.root.addWidget(self.meta)
        self.md_edit = QPlainTextEdit()
        self.md_edit.setPlaceholderText("Skill README（Markdown 源文）")
        self.root.addWidget(self.md_edit)
        self.whitelist = QLabel()
        self.whitelist.setObjectName("muted")
        self.whitelist.setWordWrap(True)
        self.root.addWidget(self.whitelist)
        self.root.addWidget(Notice("保存/试跑待接入（PATCH /skills 尚未实现），当前为只读视图"))
        self.root.addStretch()
        self._skill_id: int | None = None

    def apply_context(self, params: dict) -> None:
        self._skill_id = params.get("id")
        self.title_label.setText(f"Skill 编辑 #{self._skill_id}")

    def refresh(self) -> None:
        if not self._skill_id:
            return
        data = self.safe(lambda: self.client.skill_detail(self._skill_id))
        if data is None:
            return
        self.clear_info()
        self.meta.setText(
            f"{data.get('name')} · 产品 #{data.get('product_id')} · v{data.get('current_version')} · "
            f"{data.get('status')} / {data.get('review_policy')}"
        )
        self.md_edit.setPlainText(data.get("md") or "")
        wl = data.get("files_whitelist") or []
        self.whitelist.setText("文件白名单：" + (", ".join(wl) if wl else "（未配置）"))


# ---------- 内容包 ----------


class ContentsPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "内容包队列", parent)
        toolbar = QHBoxLayout()
        gen_btn = QPushButton("生成内容包")
        gen_btn.setEnabled(False)
        gen_btn.setToolTip("待接入：内容生成依赖未实现的业务接口")
        toolbar.addWidget(gen_btn)
        toolbar.addStretch()
        self.root.insertLayout(1, toolbar)

        self.table = DataTable(
            [("ID", "id"), ("Skill", "skill_id"), ("序号", "seq"), ("标题", "title"),
             ("状态", "status"), ("轮次", "rounds")],
            self,
        )
        self.root.addWidget(self.table)
        self.root.addWidget(Notice("内容包生成（业务编排）待接入，当前为只读视图"))
        self.root.addStretch()

    def refresh(self) -> None:
        result = self.safe(lambda: self.client.list_contents(page=1, page_size=50))
        if result is None:
            return
        rows, meta = result
        self.clear_info()
        self.table.set_rows(
            [
                {
                    "id": c.get("id"),
                    "skill_id": c.get("skill_id"),
                    "seq": c.get("seq"),
                    "title": c.get("title") or "—",
                    "status": c.get("status"),
                    "rounds": c.get("rounds"),
                }
                for c in rows
            ]
        )
        self.set_info(f"共 {meta.get('total', 0)} 个内容包")