"""工作台：对齐 frontend/src/pages/Dashboard。"""
from __future__ import annotations

from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from widgets import DataTable, Page, StatCard, StatusTag, fmt_dt
from theme import INFO, PRIMARY, STATUS_NEUTRAL_BG, SUCCESS, WARNING

STATUS_COLORS = {
    "观察中": INFO, "升温": PRIMARY, "已验证": SUCCESS,
    "降温": "#7d8794", "放弃": "#a7a7ad",
}


class DashboardPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "工作台", parent)
        self.client = client

        stats = QHBoxLayout()
        self.accounts_today = StatCard("今日分析账号", "—", PRIMARY)
        self.products_today = StatCard("今日采集商品", "—", WARNING)
        self.rising = StatCard("升温方向", "—", PRIMARY)
        self.cooling = StatCard("降温方向", "—", INFO)
        for c in (self.accounts_today, self.products_today, self.rising, self.cooling):
            stats.addWidget(c)
        self.root.addLayout(stats)

        body = QHBoxLayout()
        chart_box = QVBoxLayout()
        chart_label = QLabel("方向状态分布")
        chart_label.setObjectName("cardTitle")
        chart_box.addWidget(chart_label)
        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(240)
        chart_box.addWidget(self.chart_view)
        body.addLayout(chart_box, 3)

        right = QVBoxLayout()
        right_label = QLabel("产品方向")
        right_label.setObjectName("cardTitle")
        right.addWidget(right_label)
        self.directions_list = QVBoxLayout()
        self.directions_list.addStretch()
        right.addLayout(self.directions_list)
        right.addStretch()
        body.addLayout(right, 4)
        self.root.addLayout(body)

        recent = QLabel("近期任务")
        recent.setObjectName("cardTitle")
        self.root.addWidget(recent)
        self.runs_table = DataTable(
            [("ID", "id"), ("Agent", "agent_key"), ("状态", "status"), ("开始", "started_at"), ("结果/错误", "result")],
            self,
        )
        self.runs_table.doubleClicked.connect(lambda _: None)
        self.root.addWidget(self.runs_table)

        self.root.addStretch()
        self.refresh()

    def refresh(self) -> None:
        summary = self.safe(self.client.dashboard_summary)
        if summary is None:
            return
        self.clear_info()

        today = summary.get("accounts_today", 0)
        self.accounts_today.set_value(today)
        self.products_today.set_value(summary.get("products_today", 0))

        dirs = summary.get("directions", [])
        rising = sum(1 for d in dirs if d.get("status") == "升温")
        cooling = sum(1 for d in dirs if d.get("status") == "降温")
        self.rising.set_value(rising)
        self.cooling.set_value(cooling)
        self._render_chart(dirs)
        self._render_directions(dirs)

        runs = summary.get("recent_runs", [])
        rows = [
            {
                "id": r.get("id"),
                "agent_key": r.get("agent_key"),
                "status": r.get("status"),
                "started_at": fmt_dt(r.get("started_at")),
                "result": str(r.get("result") or r.get("error") or ""),
            }
            for r in runs
        ]
        self.runs_table.set_rows(rows)

    def _render_chart(self, dirs: list) -> None:
        counts: dict[str, int] = {}
        for d in dirs:
            counts[d.get("status", "其他")] = counts.get(d.get("status", "其他"), 0) + 1
        series = QPieSeries()
        if not counts:
            series.append("暂无数据", 1)
            series.slices()[0].setBrush(QColor(STATUS_NEUTRAL_BG))
        for status, count in counts.items():
            sl = series.append(status, count)
            sl.setBrush(QColor(STATUS_COLORS.get(status, PRIMARY)))
        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chart.setTitle("")
        self.chart_view.setChart(chart)

    def _render_directions(self, dirs: list) -> None:
        while self.directions_list.count() > 1:
            item = self.directions_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not dirs:
            lbl = QLabel("暂无方向数据")
            lbl.setObjectName("muted")
            self.directions_list.insertWidget(0, lbl)
            return
        for d in dirs[:8]:
            row = QHBoxLayout()
            name = QLabel(f"{d.get('name')} · 账号 {d.get('accounts', 0)}")
            row.addWidget(name)
            row.addStretch()
            tag = StatusTag(d.get("status"))
            row.addWidget(tag)
            w = QWidget()
            w.setLayout(row)
            self.directions_list.insertWidget(self.directions_list.count() - 1, w)
