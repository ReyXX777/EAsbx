from __future__ import annotations

import time

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy

from task_observation.models import ObservationSnapshot
from task_observation.qt.observation_bridge import ObservationBridge


@pytest.fixture
def qt_core_app():
    app = QCoreApplication.instance()

    if app is None:
        app = QCoreApplication([])

    return app


def wait_for_spy(
    app,
    spy: QSignalSpy,
    timeout_ms: int = 3000,
) -> bool:
    if spy.count() > 0:
        return True

    deadline = time.monotonic() + (timeout_ms / 1000.0)

    while time.monotonic() < deadline:
        app.processEvents()

        if spy.count() > 0:
            return True

        time.sleep(0.005)

    return False


def test_bridge_forwards_start_event_and_finish(
    tmp_path,
    qt_core_app,
) -> None:
    bridge = ObservationBridge(
        str(tmp_path),
    )

    started = QSignalSpy(
        bridge.task_started,
    )

    updated = QSignalSpy(
        bridge.observation_updated,
    )

    finished = QSignalSpy(
        bridge.task_finished,
    )

    errors = QSignalSpy(
        bridge.error,
    )

    try:
        bridge.start_task(
            "filesystem",
            metadata={
                "agent_type": "filesystem",
            },
        )

        assert wait_for_spy(
            qt_core_app,
            started,
        )

        assert started.at(0)[0] == "filesystem"

        bridge.record_event(
            "tool_started",
            {
                "tool_name": "list_directory",
                "path": ".",
            },
        )

        bridge.record_event(
            "tool_completed",
            {
                "tool_name": "list_directory",
                "path": ".",
                "success": True,
            },
        )

        bridge.finish_task()

        assert wait_for_spy(
            qt_core_app,
            finished,
        )

        assert errors.count() == 0

        snapshot = finished.at(0)[0]

        assert isinstance(
            snapshot,
            ObservationSnapshot,
        )

        assert snapshot.status == "completed"

        event_names = [event.name for event in snapshot.events]

        assert "tool_started" in event_names
        assert "tool_completed" in event_names

        continuous = {item.name: item.value for item in snapshot.continuous}

        assert continuous["total_tool_calls"] == 1.0
        assert continuous["successful_tool_calls"] == 1.0

        assert updated.count() >= 2

    finally:
        bridge.close()


def test_bridge_ignores_commands_after_close(
    tmp_path,
    qt_core_app,
) -> None:
    bridge = ObservationBridge(
        str(tmp_path),
    )

    errors = QSignalSpy(
        bridge.error,
    )

    bridge.close()

    bridge.start_task(
        "filesystem",
    )

    bridge.record_event(
        "tool_started",
    )

    bridge.finish_task()

    qt_core_app.processEvents()

    assert errors.count() == 0
