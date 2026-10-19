"""PySide6 共用控件：表格、状态标签、详情块、对话框。"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox,
    QTableView, QTextEdit, QVBoxLayout, QWidget, QComboBox,
)

from .client import ApiError


def fmt_dt(value: Any) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    return dt.strftime("%Y-%m-%d %H:%M")


def fmt_money(cents: Any) -> str:
    if cents is None:
        return "—"
    try:
        return f"¥{int(cents) / 100:.2f}"
    except (TypeError, ValueError):
        return str(cents)


def fmt_num(value: Any) -> str:
    if value is None:
        return "—"
    return f"{value:,}"


def fmt_json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, indent=2, default=str)


class TableModel(QAbstractTableModel):
    def __init__(self, columns: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.columns = columns
        self.rows: list[dict[str, Any]] = []

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel(); self.rows = rows; self.endResetModel()

    def row_data(self, row: int) -> dict[str, Any]:
        return self.rows[row] if 0 <= row < len(self.rows) else {}

    def rowCount(self, parent=QModelIndex()): return 0 if parent.isValid() else len(self.rows)
    def columnCount(self, parent=QModelIndex()): return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section][0]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        value = self.rows[index.row()].get(self.columns[index.column()][1], "")
        if role == Qt.DisplayRole:
            if isinstance(value, (dict, list)): return json.dumps(value, ensure_ascii=False)
            if value is None: return "—"
            return str(value)
        if role == Qt.TextAlignmentRole and isinstance(value, (int, float)):
            return Qt.AlignRight | Qt.AlignVCenter
        return None


class DataTable(QTableView):
    row_activated = Signal(dict)
    def __init__(self, columns: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.model_obj = TableModel(columns, self)
        self.setModel(self.model_obj)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.doubleClicked.connect(self._activate)

    def _activate(self, index: QModelIndex) -> None:
        self.row_activated.emit(self.model_obj.row_data(index.row()))

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.model_obj.set_rows(rows)
        self.resizeColumnsToContents()


class StatusTag(QLabel):
    COLORS = {
        "running": ("#e6f4ff", "#1677ff"), "pending": ("#f5f5f5", "#595959"),
        "blocked": ("#fff7e6", "#d46b08"), "done": ("#f6ffed", "#389e0d"),
        "failed": ("#fff1f0", "#cf1322"), "killed": ("#f5f5f5", "#8c8c8c"),
        "观察中": ("#f5f5f5", "#595959"), "升温": ("#fff1f0", "#cf1322"),
        "已验证": ("#f6ffed", "#389e0d"), "降温": ("#e6f4ff", "#1677ff"),
        "放弃": ("#f5f5f5", "#8c8c8c"), "draft": ("#f5f5f5", "#595959"),
        "testing": ("#fff7e6", "#d46b08"), "active": ("#f6ffed", "#389e0d"),
        "approved": ("#f6ffed", "#389e0d"), "rejected": ("#fff1f0", "#cf1322"),
        "reviewing": ("#fff7e6", "#d46b08"),
    }
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent); self.set_status(text)
    def set_status(self, text: str) -> None:
        self.setText(text or "—")
        bg, fg = self.COLORS.get(text, ("#f0f0f0", "#595959"))
        self.setStyleSheet(f"background:{bg};color:{fg};border-radius:4px;padding:2px 8px;")
        self.setAlignment(Qt.AlignCenter)


class Page(QWidget):
    """统一页面骨架。子类实现 refresh。"""
    def __init__(self, client, title: str, parent=None):
        super().__init__(parent); self.client = client; self.title = title
        self.root = QVBoxLayout(self); self.root.setContentsMargins(24, 20, 24, 24); self.root.setSpacing(14)
        top = QHBoxLayout(); self.title_label = QLabel(title); self.title_label.setObjectName("pageTitle")
        top.addWidget(self.title_label); top.addStretch(); self.refresh_btn = QPushButton("刷新"); self.refresh_btn.clicked.connect(self.refresh); top.addWidget(self.refresh_btn)
        self.root.addLayout(top)
        self.info = QLabel(); self.info.setObjectName("infoLabel"); self.info.hide(); self.root.addWidget(self.info)
    def set_info(self, text: str, error=False):
        self.info.setText(text); self.info.setProperty("error", error); self.info.style().unpolish(self.info); self.info.style().polish(self.info); self.info.show()
    def clear_info(self): self.info.hide()
    def refresh(self): pass
    def safe(self, fn):
        try: return fn()
        except ApiError as exc: self.set_info(exc.message, True); return None
        except Exception as exc: self.set_info(str(exc), True); return None


class DetailBlock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.form = QFormLayout(self); self.form.setLabelAlignment(Qt.AlignRight)
    def add(self, label: str, value: Any): self.form.addRow(QLabel(label), QLabel("—" if value is None else str(value)))
    def clear(self):
        while self.form.rowCount(): self.form.removeRow(0)


class JsonViewer(QPlainTextEdit):
    def __init__(self, value=None, parent=None):
        super().__init__(parent); self.setReadOnly(True); self.setLineWrapMode(QPlainTextEdit.NoWrap); self.setMinimumHeight(160); self.setPlainText(json.dumps(value or {}, ensure_ascii=False, indent=2, default=str))


class Notice(QWidget):
    def __init__(self, text="待接入", parent=None):
        super().__init__(parent); layout=QHBoxLayout(self); layout.setContentsMargins(0,0,0,0); label=QLabel(text); label.setObjectName("notice"); layout.addWidget(label); layout.addStretch()


class TaskDialog(QDialog):
    def __init__(self, agents: list[dict], parent=None):
        super().__init__(parent); self.setWindowTitle("发起任务"); self.setMinimumWidth(420)
        form=QFormLayout(self); self.agent=QComboBox(); self.agent.setEditable(False)
        for a in agents: self.agent.addItem(f"{a.get('name', a.get('key'))} · {a.get('key')}", a.get("key"))
        self.product=QSpinBox(); self.product.setRange(0, 2_000_000); self.product.setSpecialValueText("无")
        self.context=QTextEdit(); self.context.setPlaceholderText("初始上下文（可选）"); self.context.setFixedHeight(100)
        form.addRow("Agent", self.agent); form.addRow("产品 ID", self.product); form.addRow("上下文", self.context)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)
    def values(self): return self.agent.currentData(), (self.product.value() or None), self.context.toPlainText().strip() or None


class ReviewPointDialog(QDialog):
    acted = Signal(int, str, str)  # point_id, action, note
    def __init__(self, points: list[dict], parent=None):
        super().__init__(parent); self.setWindowTitle("待审核"); self.setMinimumSize(620, 440); self.points=points
        root=QVBoxLayout(self); self.list=QListWidget();
        for p in points: self.list.addItem(QListWidgetItem(f"#{p.get('id')} · {p.get('rtype')} · Run #{p.get('run_id')}"))
        root.addWidget(self.list); self.viewer=JsonViewer(); root.addWidget(self.viewer)
        self.note=QLineEdit(); self.note.setPlaceholderText("审核备注（可选）"); root.addWidget(self.note)
        buttons=QDialogButtonBox(); passed=buttons.addButton("通过并继续", QDialogButtonBox.AcceptRole); rejected=buttons.addButton("驳回", QDialogButtonBox.DestructiveRole); buttons.addButton(QDialogButtonBox.Close)
        passed.clicked.connect(lambda: self._act("passed")); rejected.clicked.connect(lambda: self._act("rejected")); buttons.rejected.connect(self.reject); root.addWidget(buttons); self.list.currentRowChanged.connect(self._select); self.list.setCurrentRow(0)
    def _select(self, row):
        if 0 <= row < len(self.points): self.viewer.setPlainText(json.dumps(self.points[row].get("payload",{}), ensure_ascii=False, indent=2, default=str))
    def _act(self, action):
        if 0 <= self.list.currentRow() < len(self.points):
            point_id = int(self.points[self.list.currentRow()].get("id"))
            self.acted.emit(point_id, action, self.note.text().strip())
            self.accept()


class MessageDialog(QDialog):
    def __init__(self, messages: list, tool_calls: list, parent=None):
        super().__init__(parent); self.setWindowTitle("任务消息"); self.resize(720, 560); root=QVBoxLayout(self)
        view=QPlainTextEdit(); view.setReadOnly(True); view.setLineWrapMode(QPlainTextEdit.NoWrap); view.setPlainText(json.dumps({"messages": messages, "tool_calls": tool_calls}, ensure_ascii=False, indent=2, default=str)); root.addWidget(view)
        b=QDialogButtonBox(QDialogButtonBox.Close); b.rejected.connect(self.reject); root.addWidget(b)


class ConfirmDialog(QDialog):
    def __init__(self, text: str, parent=None):
        super().__init__(parent); self.setWindowTitle("确认"); layout=QVBoxLayout(self); layout.addWidget(QLabel(text)); b=QDialogButtonBox(QDialogButtonBox.Yes|QDialogButtonBox.No); b.accepted.connect(self.accept); b.rejected.connect(self.reject); layout.addWidget(b)


class StatCard(QWidget):
    def __init__(self, title: str, value: Any = 0, accent: str = "#1677ff", parent=None):
        super().__init__(parent); layout=QVBoxLayout(self); layout.setContentsMargins(18,14,18,14); self.setObjectName("statCard")
        t=QLabel(title); t.setObjectName("muted"); self.value=QLabel(str(value)); self.value.setObjectName("statValue"); self.value.setStyleSheet(f"color:{accent};"); layout.addWidget(t); layout.addWidget(self.value)
    def set_value(self, value): self.value.setText(str(value))
