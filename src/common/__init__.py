"""Common zero-Qt building blocks for the workbench.

This package never imports PySide6, so tests can exercise the service graph
headlessly. It lives under ``src/`` next to ``core``/``services`` (src-layout).
"""

from common.events import EventHub
from common.context import AppContext

__all__ = ["EventHub", "AppContext"]