"""架构层单测：common 事件 / tasks 状态机 / bootstrap 装配（零 Qt）。"""
from __future__ import annotations

import time

import pytest

from common.events import EventHub
from tasks import TaskManager, TaskState


# ---- EventHub ------------------------------------------------------ #

def test_eventhub_sub_and_publish():
    hub = EventHub()
    seen = []
    unsub = hub.subscribe("demo", lambda ev: seen.append(ev))
    hub.publish("demo", x=1)
    unsub()
    hub.publish("demo", x=2)
    assert len(seen) == 1
    assert seen[0]["type"] == "demo"
    assert seen[0]["x"] == 1


def test_eventhub_wildcard():
    hub = EventHub()
    seen = []
    hub.subscribe("*", lambda ev: seen.append(ev["type"]))
    hub.publish("a")
    hub.publish("b")
    assert seen == ["a", "b"]


# ---- TaskManager --------------------------------------------------- #

def test_submit_done_and_result():
    tm = TaskManager(max_workers=2)
    events = []
    tm.subscribe(lambda ev: events.append(ev["type"]))

    def work(*, cancel_event, **kwargs):
        time.sleep(0.02)
        return 42

    task = tm.submit(work, label="calc")
    deadline = time.time() + 3
    while task.state not in (TaskState.DONE, TaskState.FAILED) and time.time() < deadline:
        time.sleep(0.005)
    tm.shutdown()
    assert task.result == 42
    assert task.state == TaskState.DONE
    assert "started" in events
    assert "done" in events


def test_submit_failed_sets_error():
    tm = TaskManager(max_workers=1)

    def boom(*, cancel_event, **kwargs):
        raise ValueError("boom")

    task = tm.submit(boom, label="fail")
    deadline = time.time() + 2
    while task.state not in (TaskState.DONE, TaskState.FAILED) and time.time() < deadline:
        time.sleep(0.005)
    tm.shutdown()
    assert task.state == TaskState.FAILED
    assert task.error == "boom"


def test_cancel_sets_cooperative_flag():
    tm = TaskManager(max_workers=1)
    task = tm.submit(
        lambda *, cancel_event, **kwargs: cancel_event.wait(2),
        label="block",
    )
    time.sleep(0.03)
    assert tm.cancel(task.id)
    assert task.cancel_event.is_set()
    tm.shutdown(wait=False)


# ---- bootstrap ------------------------------------------------------ #

def test_build_context_assembles():
    """bootstrap env side effects are applied first; context resolves."""
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ["RUN_EXECUTOR"] = "inline"

    import bootstrap  # noqa: F401  (applies side effects)

    from common.context import AppContext

    ctx = bootstrap.build_context()
    assert isinstance(ctx, AppContext)
    assert ctx.events is not None
    assert ctx.tasks is not None
    assert ctx.settings is not None
    ctx.tasks.shutdown(wait=False)