"""设置：对齐 frontend/src/pages/Settings（只读视图）。"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout

from src.widgets import DataTable, DetailBlock, Page, fmt_dt


class SettingsPage(Page):
    def __init__(self, client, parent=None):
        super().__init__(client, "设置", parent)

        executor_title = QLabel("任务执行器")
        executor_title.setObjectName("cardTitle")
        self.root.addWidget(executor_title)
        executor = DetailBlock()
        executor.add("运行模式", "inline（进程内守护线程，无需 Redis/Celery）")
        executor.add("说明", "桌面版固定使用 inline；任务进度通过 WebSocket 实时推送到界面")
        self.root.addWidget(executor)

        agent_title = QLabel("Agent 定义")
        agent_title.setObjectName("cardTitle")
        self.root.addWidget(agent_title)
        self.agent_table = DataTable(
            [("Key", "key"), ("名称", "name"), ("模型", "model"), ("工具", "tool_keys"), ("启用", "is_enabled")],
            self,
        )
        self.root.addWidget(self.agent_table)

        risk_title = QLabel("风控节奏（随机延迟区间）")
        risk_title.setObjectName("cardTitle")
        self.root.addWidget(risk_title)
        self.risk_table = DataTable(
            [("Scope", "scope"), ("最小延迟(s)", "min_delay_s"), ("最大延迟(s)", "max_delay_s"), ("重试上限", "retry_max"), ("启用", "enabled")],
            self,
        )
        self.root.addWidget(self.risk_table)

        self.root.addStretch()
        self.refresh()

    def refresh(self) -> None:
        agents = self.safe(self.client.agent_defs)
        if agents is None:
            return
        self.agent_table.set_rows(
            [
                {
                    "key": a.get("key"),
                    "name": a.get("name"),
                    "model": a.get("model"),
                    "tool_keys": ", ".join(a.get("tool_keys") or []),
                    "is_enabled": "是" if a.get("is_enabled") else "否",
                }
                for a in agents
            ]
        )
        risks = self.safe(self.client.risk_config)
        if risks is not None:
            self.risk_table.set_rows(
                [
                    {
                        "scope": r.get("scope"),
                        "min_delay_s": r.get("min_delay_s"),
                        "max_delay_s": r.get("max_delay_s"),
                        "retry_max": r.get("retry_max"),
                        "enabled": "是" if r.get("enabled") else "否",
                    }
                    for r in risks
                ]
            )
