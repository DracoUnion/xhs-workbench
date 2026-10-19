"""任务中心：对齐 frontend/src/pages/TaskCenter。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.client import ApiError
from src.widgets import (
    ConfirmDialog, DataTable, JsonViewer, MessageDialog, Page,
    ReviewPointDialog, StatusTag, TaskDialog, fmt_dt,
)

STATUSES = ["", "pending", "running", "blocked", "done", "failed", "killed"]
STATUS_LABELS = {
    "": "全部状态", "pending": "待执行", "running": "运行中", "blocked": "待审核",
    "done": "已完成", "failed": "失败", "killed": "已终止",
}


class TaskCenterPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "任务中心", parent)
        self._live: dict[int, str] = {}
        self._selected: dict | None = None

        # 顶部工具栏（在 Page 自带标题/刷新之外追加过滤器与操作）
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("状态"))
        self.status_combo = QComboBox()
        for key, label in STATUS_LABELS.items():
            self.status_combo.addItem(label, key)
        self.status_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_combo)
        toolbar.addStretch()

        self.review_btn = QPushButton("待审核 (0)")
        self.review_btn.clicked.connect(self._open_review)
        toolbar.addWidget(self.review_btn)

        self.create_btn = QPushButton("发起任务")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.clicked.connect(self._create_task)
        toolbar.addWidget(self.create_btn)

        # 插入工具栏：在 Page.root 中标题行之后
        self.root.insertLayout(1, toolbar)

        self.table = DataTable(
            [
                ("ID", "id"), ("Agent", "agent_key"), ("产品", "product_id"),
                ("状态", "status"), ("开始", "started_at"), ("完成", "finished_at"),
                ("结果/错误", "result"),
            ],
            self,
        )
        self.table.clicked.connect(self._select_row)
        self.table.doubleClicked.connect(self._messages)
        self.root.addWidget(self.table)

        actions = QHBoxLayout()
        self.selected_label = QLabel("未选择任务")
        self.selected_label.setObjectName("muted")
        actions.addWidget(self.selected_label)
        actions.addStretch()
        self.messages_btn = QPushButton("消息")
        self.messages_btn.clicked.connect(self._messages)
        self.resume_btn = QPushButton("恢复")
        self.resume_btn.clicked.connect(self._resume)
        self.abort_btn = QPushButton("终止")
        self.abort_btn.clicked.connect(self._abort)
        for b in (self.messages_btn, self.resume_btn, self.abort_btn):
            b.setEnabled(False)
            actions.addWidget(b)
        self.root.addLayout(actions)

        self.refresh()

    # ---------- 数据 ----------

    def refresh(self) -> None:
        status = self.status_combo.currentData()
        result = self.safe(lambda: self.client.list_tasks(status=status or None, page=1, page_size=50))
        if result is None:
            return
        items, meta = result
        self.clear_info()
        rows = []
        for r in items:
            run_id = int(r.get("id") or 0)
            status_text = self._live.get(run_id, r.get("status"))
            error = (r.get("error") or {}).get("message") if isinstance(r.get("error"), dict) else r.get("error")
            result_text = r.get("result")
            if isinstance(result_text, dict) and result_text:
                result_text = str(result_text.get("text") or result_text)
            rows.append(
                {
                    "id": run_id,
                    "agent_key": r.get("agent_key"),
                    "product_id": r.get("product_id") or "—",
                    "status": status_text,
                    "started_at": fmt_dt(r.get("started_at")),
                    "finished_at": fmt_dt(r.get("finished_at")),
                    "result": error or (str(result_text)[:80] if result_text else "—"),
                }
            )
        self.table.set_rows(rows)
        if rows and self._selected:
            for row in rows:
                if row["id"] == self._selected.get("id"):
                    self._selected = row
        self._refresh_review_badge()

    def on_event(self, event: dict) -> None:
        """WS 事件 → 实时刷新（对齐 useTaskWebSocket 的 version 机制）。"""
        etype = event.get("type", "")
        data = event.get("data", {}) or {}
        run_id = data.get("run_id")
        if etype.startswith("run.") and run_id is not None:
            if etype == "run.progress":
                self._live[int(run_id)] = "running"
            elif etype == "run.blocked":
                self._live[int(run_id)] = "blocked"
            elif etype == "run.done":
                self._live[int(run_id)] = "done"
            elif etype == "run.failed":
                self._live[int(run_id)] = "failed"
            self.refresh()
        elif etype == "run.blocked":
            self._refresh_review_badge()

    # ---------- 选择与操作 ----------

    def _select_row(self, index) -> None:
        row = self.table.model_obj.row_data(index.row())
        self._selected = row
        self.selected_label.setText(f"Run #{row.get('id')} · {row.get('agent_key')} · {row.get('status')}")
        self.messages_btn.setEnabled(bool(row.get("id")))
        status = row.get("status")
        self.resume_btn.setEnabled(status in ("blocked", "failed", "pending"))
        self.abort_btn.setEnabled(status in ("pending", "running", "blocked"))

    def _messages(self) -> None:
        if not self._selected:
            return
        run_id = int(self._selected["id"])
        data = self.safe(lambda: self.client.get_task_messages(run_id))
        if data is None:
            return
        messages, tool_calls = data
        MessageDialog(messages, tool_calls, self).exec()

    def _create_task(self) -> None:
        agents = self.safe(self.client.agent_defs)
        if not agents:
            self.set_info("暂无可用 Agent（seed 未就绪？）", True)
            return
        dialog = TaskDialog(agents, self)
        if dialog.exec() != dialog.Accepted:
            return
        agent_key, product_id, context = dialog.values()
        result = self.safe(lambda: self.client.create_task(agent_key, product_id=product_id, context=context))
        if result:
            self.set_info(f"已发起任务 Run #{result.get('run_id')}（mode={result.get('mode')}）")
            self.refresh()

    def _resume(self) -> None:
        if not self._selected:
            return
        run_id = int(self._selected["id"])
        result = self.safe(lambda: self.client.resume_task(run_id))
        if result:
            self.set_info(f"Run #{run_id} 已恢复（mode={result.get('data', {}).get('mode') if isinstance(result.get('data'), dict) else ''}）")
            self.refresh()

    def _abort(self) -> None:
        if not self._selected:
            return
        run_id = int(self._selected["id"])
        dialog = ConfirmDialog(f"确定终止 Run #{run_id}？", self)
        if dialog.exec() != dialog.Accepted:
            return
        result = self.safe(lambda: self.client.abort_task(run_id))
        if result:
            self.set_info(f"Run #{run_id} 已终止")
            self.refresh()

    # ---------- 审核点 ----------

    def _refresh_review_badge(self) -> None:
        points = self.safe(self.client.list_review_points)
        if points is None:
            return
        self.review_btn.setText(f"待审核 ({len(points)})")

    def _open_review(self) -> None:
        points = self.safe(self.client.list_review_points)
        if points is None:
            return
        if not points:
            self.set_info("没有待审核的点")
            return
        dialog = ReviewPointDialog(points, self)
        dialog.acted.connect(self._act_review)
        dialog.exec()

    def _act_review(self, point_id: int, action: str, note: str) -> None:
        result = self.safe(lambda: self.client.act_review_point(point_id, action, note))
        if result:
            self.set_info(f"审核点 #{point_id} 已处理（{action}）")
            self.refresh()
