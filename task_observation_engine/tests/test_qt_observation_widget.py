from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from task_observation.models import (
    ContinuousObservation,
    DiscreteObservation,
    ObservationSnapshot,
    TaskEvent,
    TaskIdentity,
    TracePoint,
)
from task_observation.qt.observation_widget import ObservationWidget


@pytest.fixture
def qt_app():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def make_snapshot() -> ObservationSnapshot:
    identity = TaskIdentity(
        session_id="qt-test-session",
        family_key="filesystem",
        task_key="",
        started_at="2026-10-03T13:03:33+00:00",
    )

    return ObservationSnapshot(
        identity=identity,
        started_at="2026-10-03T13:03:33+00:00",
        finished_at="2026-10-03T13:03:43+00:00",
        status="completed",
        metadata={
            "agent_type": "filesystem",
        },
        discrete=(
            DiscreteObservation(
                name="task_status",
                value="completed",
            ),
            DiscreteObservation(
                name="task_completed",
                value=True,
            ),
        ),
        continuous=(
            ContinuousObservation(
                name="total_tool_calls",
                value=4.0,
            ),
            ContinuousObservation(
                name="compute_count",
                value=1.0,
            ),
        ),
        events=(
            TaskEvent(
                name="tool_completed",
                source="filesystem_worker",
                payload={
                    "tool_name": "read_table",
                    "path": "Employees.csv",
                    "success": True,
                },
            ),
        ),
        traces=(
            TracePoint(
                sequence=0,
                timestamp="2026-10-03T13:03:34+00:00",
                phase="tool_started",
                action="read_table",
                path="Employees.csv",
                discrete={
                    "tool_name": "read_table",
                },
            ),
        ),
    )


def test_widget_displays_snapshot(
    tmp_path,
    qt_app,
) -> None:
    widget = ObservationWidget(
        str(tmp_path),
    )

    try:
        snapshot = make_snapshot()

        widget._display_snapshot(
            snapshot,
        )

        assert widget.session_id_label.text() == ("qt-test-session")

        assert widget.family_label.text() == ("filesystem")

        assert widget.session_status_label.text() == ("completed")

        assert widget.discrete_table.rowCount() == 2

        assert widget.feature_selector.count() == 2

        assert widget.feature_selector.itemText(0) == ("total_tool_calls")

        assert widget.feature_selector.itemText(1) == ("compute_count")

        assert widget.event_table.rowCount() == 2

    finally:
        widget.close()


def test_widget_displays_actual_event_and_trace_attributes(
    tmp_path,
    qt_app,
) -> None:
    widget = ObservationWidget(
        str(tmp_path),
    )

    try:
        snapshot = make_snapshot()

        widget._display_snapshot(
            snapshot,
        )

        # TaskEvent
        assert (
            widget.event_table.item(
                0,
                0,
            ).text()
            == "event"
        )

        assert (
            widget.event_table.item(
                0,
                1,
            ).text()
            == "tool_completed"
        )

        assert (
            widget.event_table.item(
                0,
                2,
            ).text()
            == "filesystem_worker"
        )

        # TracePoint
        assert (
            widget.event_table.item(
                1,
                0,
            ).text()
            == "tool_started"
        )

        assert (
            widget.event_table.item(
                1,
                1,
            ).text()
            == "read_table"
        )

        assert (
            widget.event_table.item(
                1,
                2,
            ).text()
            == "Employees.csv"
        )

    finally:
        widget.close()


def test_widget_selects_continuous_feature_for_plot(
    tmp_path,
    qt_app,
) -> None:
    widget = ObservationWidget(
        str(tmp_path),
    )

    try:
        snapshot = make_snapshot()

        widget._display_snapshot(
            snapshot,
        )

        widget.feature_selector.setCurrentText(
            "compute_count",
        )

        assert widget.plot._title == "compute_count"
        assert widget.plot._values == [1.0]

    finally:
        widget.close()


def test_widget_replays_persisted_session(
    tmp_path,
    qt_app,
) -> None:
    from task_observation import TaskObservationEngine

    engine = TaskObservationEngine(
        tmp_path,
    )

    session = engine.start(
        "filesystem",
    )

    session.events.event(
        "tool_started",
        source="filesystem_worker",
        payload={
            "tool_name": "search_files",
            "path": ".",
        },
    )

    session.events.event(
        "tool_completed",
        source="filesystem_worker",
        payload={
            "tool_name": "search_files",
            "path": ".",
            "success": True,
        },
    )

    snapshot = session.finish()

    widget = ObservationWidget(
        str(tmp_path),
    )

    try:
        widget.refresh_history()

        assert widget.history_list.count() == 1

        item = widget.history_list.item(0)

        widget._load_history_item(
            item,
        )

        assert widget._snapshot is not None

        assert widget._snapshot.identity.session_id == snapshot.identity.session_id

        assert widget.session_status_label.text() == "completed"

        continuous = {item.name: item.value for item in widget._snapshot.continuous}

        assert continuous["total_tool_calls"] == 1.0

        assert continuous["search_files_count"] == 1.0

    finally:
        widget.close()
