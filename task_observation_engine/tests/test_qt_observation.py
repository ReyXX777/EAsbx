from __future__ import annotations

import os
from pathlib import Path

import pytest

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from task_observation import ReplayAPI, TaskObservationEngine
from task_observation.qt import (
    ObservationBridge,
    ObservationPlot,
    ObservationWidget,
    ObservationWorker,
)

# ============================================================================
# Qt application fixture
# ============================================================================


@pytest.fixture(scope="session")
def qapp():
    os.environ.setdefault(
        "QT_QPA_PLATFORM",
        "offscreen",
    )

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


# ============================================================================
# Qt package exports
# ============================================================================


def test_qt_package_exports_public_components():
    from task_observation import qt

    assert qt.ObservationBridge is ObservationBridge
    assert qt.ObservationPlot is ObservationPlot
    assert qt.ObservationWorker is ObservationWorker
    assert qt.ObservationWidget is ObservationWidget


# ============================================================================
# ObservationPlot
# ============================================================================


def test_observation_plot_accepts_numeric_values(qapp):
    plot = ObservationPlot()

    plot.set_data(
        [
            1.0,
            2.0,
            3.0,
            5.0,
        ],
        "row_count",
    )

    assert plot._values == [
        1.0,
        2.0,
        3.0,
        5.0,
    ]

    assert plot._title == "row_count"


def test_observation_plot_filters_invalid_values(qapp):
    plot = ObservationPlot()

    plot.set_data(
        [
            1.0,
            None,
            float("nan"),
            float("inf"),
            -float("inf"),
            "2.5",
            "not-a-number",
        ],
        "test_feature",
    )

    assert plot._values == [
        1.0,
        2.5,
    ]


def test_observation_plot_clear_removes_values(qapp):
    plot = ObservationPlot()

    plot.set_data(
        [
            10.0,
            20.0,
        ],
        "value",
    )

    assert plot._values == [
        10.0,
        20.0,
    ]

    plot.clear()

    assert plot._values == []


def test_observation_plot_paints_without_values(qapp):
    plot = ObservationPlot()

    plot.resize(
        500,
        300,
    )

    plot.show()

    qapp.processEvents()
    plot.repaint()

    assert plot._values == []


def test_observation_plot_paints_single_value(qapp):
    plot = ObservationPlot()

    plot.set_data(
        [42.0],
        "single_value",
    )

    plot.resize(
        500,
        300,
    )

    plot.show()

    qapp.processEvents()
    plot.repaint()

    assert plot._values == [42.0]


# ============================================================================
# ObservationWorker
# ============================================================================


def test_observation_worker_starts_session(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    started = []
    errors = []

    worker.task_started.connect(
        started.append,
    )

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    assert errors == []
    assert started == [
        "filesystem",
    ]

    assert worker._session is not None
    assert worker._session.identity.family_key == "filesystem"

    worker.shutdown()


def test_observation_worker_rejects_empty_family(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "   ",
    )

    assert worker._session is None
    assert len(errors) == 1
    assert "task family" in errors[0].lower()

    worker.shutdown()


def test_observation_worker_rejects_second_active_session(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.start_task(
        "browser",
    )

    assert worker._session is not None
    assert worker._session.identity.family_key == "filesystem"

    assert len(errors) == 1
    assert "another task is active" in errors[0].lower()

    worker.shutdown()


def test_observation_worker_records_discrete_observation(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_discrete(
        "approval_label",
        True,
    )

    assert errors == []

    snapshot = worker._session.snapshot()

    assert any(
        item.name == "approval_label" and item.value is True
        for item in snapshot.discrete
    )

    worker.shutdown()


def test_observation_worker_records_continuous_observation(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_continuous(
        "row_count",
        1000,
    )

    assert errors == []

    snapshot = worker._session.snapshot()

    assert any(
        item.name == "row_count" and item.value == 1000.0
        for item in snapshot.continuous
    )

    worker.shutdown()


def test_observation_worker_preserves_missing_values(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_discrete(
        "optional",
        None,
    )

    worker.record_continuous(
        "optional_number",
        None,
    )

    worker.record_continuous(
        "bad_number",
        "not-a-number",
    )

    assert errors == []

    snapshot = worker._session.snapshot()

    optional = [item for item in snapshot.discrete if item.name == "optional"]

    optional_number = [
        item for item in snapshot.continuous if item.name == "optional_number"
    ]

    bad_number = [item for item in snapshot.continuous if item.name == "bad_number"]

    assert len(optional) == 1
    assert optional[0].value is None

    assert len(optional_number) == 1
    assert optional_number[0].value is None

    assert len(bad_number) == 1
    assert bad_number[0].value is None

    worker.shutdown()


def test_observation_worker_publishes_current_snapshot(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    snapshots = []
    errors = []

    worker.observation_updated.connect(
        snapshots.append,
    )

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_discrete(
        "approval_label",
        True,
    )

    worker.publish_current_state()

    assert errors == []
    assert len(snapshots) == 2

    snapshot = snapshots[-1]

    assert snapshot.identity.family_key == "filesystem"
    assert snapshot.status == "running"

    assert any(
        item.name == "approval_label" and item.value is True
        for item in snapshot.discrete
    )

    worker.shutdown()


def test_observation_worker_does_nothing_when_publishing_without_session(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    snapshots = []
    errors = []

    worker.observation_updated.connect(
        snapshots.append,
    )

    worker.worker_error.connect(
        errors.append,
    )

    worker.publish_current_state()

    assert snapshots == []
    assert errors == []

    worker.shutdown()


def test_observation_worker_records_event(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_event(
        "tool_started",
        {
            "tool_name": "list_directory",
            "path": ".",
        },
    )

    assert errors == []

    snapshot = worker._session.snapshot()

    assert len(snapshot.events) == 1

    event = snapshot.events[0]

    assert event.name == "tool_started"
    assert event.source == "qt_observation_worker"

    assert event.payload == {
        "tool_name": "list_directory",
        "path": ".",
    }

    worker.shutdown()


def test_observation_worker_record_event_requires_active_session(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.record_event(
        "tool_started",
        {
            "tool_name": "list_directory",
        },
    )

    assert len(errors) == 1
    assert "no active observation session" in errors[0].lower()

    worker.shutdown()


def test_observation_worker_finish_produces_derived_snapshot(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    finished = []
    updated = []
    errors = []

    worker.task_finished.connect(
        finished.append,
    )

    worker.observation_updated.connect(
        updated.append,
    )

    worker.worker_error.connect(
        errors.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_event(
        "tool_started",
        {
            "tool_name": "search_files",
            "path": ".",
        },
    )

    worker.record_event(
        "tool_completed",
        {
            "tool_name": "search_files",
            "path": ".",
            "success": True,
        },
    )

    worker.finish_task()

    assert errors == []
    assert len(finished) == 1
    assert len(updated) == 2

    snapshot = finished[0]

    assert snapshot.status == "completed"

    continuous = {item.name: item.value for item in snapshot.continuous}

    discrete = {item.name: item.value for item in snapshot.discrete}

    assert continuous["total_tool_calls"] == 1.0
    assert continuous["successful_tool_calls"] == 1.0
    assert continuous["failed_tool_calls"] == 0.0
    assert continuous["search_files_count"] == 1.0

    assert discrete["task_status"] == "completed"
    assert discrete["task_completed"] is True
    assert discrete["task_failed"] is False
    assert discrete["used_search"] is True

    assert worker._session is None

    worker.shutdown()


def test_observation_worker_persists_finished_snapshot(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    finished = []

    worker.task_finished.connect(
        finished.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_event(
        "tool_started",
        {
            "tool_name": "read_table",
            "path": "Employees.csv",
        },
    )

    worker.record_event(
        "tool_completed",
        {
            "tool_name": "read_table",
            "path": "Employees.csv",
            "success": True,
        },
    )

    worker.finish_task()

    assert len(finished) == 1

    snapshot = finished[0]

    worker.shutdown()

    replay = ReplayAPI(
        tmp_path,
    )

    loaded = replay.session(
        snapshot.identity.session_id,
    )

    assert loaded.identity.session_id == snapshot.identity.session_id
    assert loaded.status == "completed"

    continuous = {item.name: item.value for item in loaded.continuous}

    assert continuous["total_tool_calls"] == 1.0
    assert continuous["successful_tool_calls"] == 1.0
    assert continuous["read_table_count"] == 1.0


def test_observation_worker_rejects_finish_without_session(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = []

    worker.worker_error.connect(
        errors.append,
    )

    worker.finish_task()

    assert len(errors) == 1
    assert "no active observation session" in errors[0].lower()

    worker.shutdown()


def test_observation_worker_shutdown_releases_session(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    worker.start_task(
        "filesystem",
    )

    assert worker._session is not None

    worker.shutdown()

    assert worker._session is None


# ============================================================================
# ObservationBridge
# ============================================================================


def test_observation_bridge_creates_worker_thread(
    qapp,
    tmp_path: Path,
):
    bridge = ObservationBridge(
        str(tmp_path),
    )

    try:
        assert bridge._worker is not None
        assert bridge._thread.isRunning()
    finally:
        bridge.close()

    assert not bridge._thread.isRunning()


def test_observation_bridge_close_is_idempotent(
    qapp,
    tmp_path: Path,
):
    bridge = ObservationBridge(
        str(tmp_path),
    )

    bridge.close()
    bridge.close()

    assert not bridge._thread.isRunning()


def test_observation_bridge_starts_worker_session(
    qapp,
    tmp_path: Path,
):
    bridge = ObservationBridge(
        str(tmp_path),
    )

    try:
        started = QSignalSpy(
            bridge.task_started,
        )

        bridge.start_task(
            "filesystem",
        )

        assert started.wait(2000)
        assert started.count() == 1
        assert started.at(0)[0] == "filesystem"

    finally:
        bridge.close()


def test_observation_bridge_finishes_worker_session(
    qapp,
    tmp_path: Path,
):
    bridge = ObservationBridge(
        str(tmp_path),
    )

    try:
        started = QSignalSpy(
            bridge.task_started,
        )

        finished = QSignalSpy(
            bridge.task_finished,
        )

        errors = QSignalSpy(
            bridge.error,
        )

        bridge.start_task(
            "filesystem",
        )

        assert started.wait(2000)
        assert started.count() == 1
        assert started.at(0)[0] == "filesystem"

        bridge.record_event(
            "tool_started",
            {
                "tool_name": "search_files",
                "path": ".",
            },
        )

        bridge.record_event(
            "tool_completed",
            {
                "tool_name": "search_files",
                "path": ".",
                "success": True,
            },
        )

        bridge.finish_task()

        assert finished.wait(2000)
        assert finished.count() == 1
        assert errors.count() == 0

        snapshot = finished.at(0)[0]

        assert snapshot.status == "completed"
        assert snapshot.identity.family_key == "filesystem"

        continuous = {item.name: item.value for item in snapshot.continuous}

        assert continuous["total_tool_calls"] == 1.0
        assert continuous["successful_tool_calls"] == 1.0
        assert continuous["search_files_count"] == 1.0

    finally:
        bridge.close()


# ============================================================================
# ObservationWidget construction and initial state
# ============================================================================


def test_observation_widget_can_be_created(
    qapp,
    tmp_path: Path,
):
    widget = ObservationWidget(
        tmp_path,
    )

    try:
        assert widget.bridge is not None
        assert widget.plot is not None
        assert widget.history_list is not None
        assert widget.discrete_table is not None
        assert widget.event_table is not None
    finally:
        widget.bridge.close()


def test_observation_widget_initial_state(
    qapp,
    tmp_path: Path,
):
    widget = ObservationWidget(
        tmp_path,
    )

    try:
        assert widget._snapshot is None

        assert widget.status_label.text() == "No active observation."

        assert widget.session_id_label.text() == "-"
        assert widget.family_label.text() == "-"
        assert widget.session_status_label.text() == "-"

        assert widget.history_list.count() == 0

        assert widget.feature_selector.count() == 0
        assert widget.plot._values == []
    finally:
        widget.bridge.close()


# ============================================================================
# ObservationWidget snapshot display
# ============================================================================


def test_observation_widget_displays_snapshot(
    qapp,
    tmp_path: Path,
):
    engine = TaskObservationEngine(
        tmp_path,
    )

    session = engine.start(
        "filesystem",
    )

    session.discrete.record(
        "approval_label",
        True,
    )

    session.continuous.record(
        "row_count",
        1000,
    )

    session.events.event(
        "tool_completed",
        source="filesystem_worker",
        payload={
            "tool_name": "read_table",
            "path": "Employees.csv",
            "success": True,
        },
    )

    snapshot = session.finish()

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget._display_snapshot(
            snapshot,
        )

        assert widget._snapshot is snapshot

        assert widget.session_id_label.text() == snapshot.identity.session_id

        assert widget.family_label.text() == "filesystem"
        assert widget.session_status_label.text() == "completed"

        assert widget.discrete_table.rowCount() >= 1

        discrete_rows = []

        for row in range(
            widget.discrete_table.rowCount(),
        ):
            discrete_rows.append(
                (
                    widget.discrete_table.item(
                        row,
                        0,
                    ).text(),
                    widget.discrete_table.item(
                        row,
                        1,
                    ).text(),
                )
            )

        assert (
            "approval_label",
            "True",
        ) in discrete_rows

        feature_names = [
            widget.feature_selector.itemText(index)
            for index in range(
                widget.feature_selector.count(),
            )
        ]

        assert "row_count" in feature_names

        widget.feature_selector.setCurrentText(
            "row_count",
        )

        assert widget.plot._title == "row_count"
        assert widget.plot._values == [1000.0]

    finally:
        widget.bridge.close()


def test_observation_widget_displays_missing_discrete_value(
    qapp,
    tmp_path: Path,
):
    engine = TaskObservationEngine(
        tmp_path,
    )

    session = engine.start(
        "filesystem",
    )

    session.discrete.record(
        "optional",
        None,
    )

    snapshot = session.finish()

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget._display_snapshot(
            snapshot,
        )

        values = []

        for row in range(
            widget.discrete_table.rowCount(),
        ):
            values.append(
                widget.discrete_table.item(
                    row,
                    1,
                ).text()
            )

        assert "<missing>" in values

    finally:
        widget.bridge.close()


def test_observation_widget_displays_events_and_traces(
    qapp,
    tmp_path: Path,
):
    engine = TaskObservationEngine(
        tmp_path,
    )

    session = engine.start(
        "filesystem",
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

    session.events.trace(
        "tool_completed",
        action="search_files",
        path=".",
        discrete={
            "success": True,
        },
    )

    snapshot = session.finish()

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget._display_snapshot(
            snapshot,
        )

        assert widget.event_table.rowCount() == (
            len(snapshot.events) + len(snapshot.traces)
        )

        event_text = []

        for row in range(
            widget.event_table.rowCount(),
        ):
            event_text.append(
                (
                    widget.event_table.item(
                        row,
                        0,
                    ).text(),
                    widget.event_table.item(
                        row,
                        1,
                    ).text(),
                    widget.event_table.item(
                        row,
                        2,
                    ).text(),
                )
            )

        assert any(row[0] == "tool_completed" for row in event_text)

        assert any(row[1] == "search_files" for row in event_text)

    finally:
        widget.bridge.close()


# ============================================================================
# ObservationWidget persistent replay
# ============================================================================


def test_observation_widget_loads_persisted_history(
    qapp,
    tmp_path: Path,
):
    engine = TaskObservationEngine(
        tmp_path,
    )

    session = engine.start(
        "filesystem",
    )

    session.discrete.record(
        "approval_label",
        True,
    )

    snapshot = session.finish()

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget.refresh_history()

        assert widget.history_list.count() == 1

        item = widget.history_list.item(
            0,
        )

        assert (
            item.data(
                Qt.ItemDataRole.UserRole,
            )
            == snapshot.identity.session_id
        )

        widget._load_history_item(
            item,
        )

        assert widget._snapshot is not None

        assert widget._snapshot.identity.session_id == snapshot.identity.session_id

        assert widget.session_id_label.text() == (snapshot.identity.session_id)

        assert widget.family_label.text() == "filesystem"
        assert widget.session_status_label.text() == "completed"

    finally:
        widget.bridge.close()


def test_observation_widget_refresh_history_reads_replay_api(
    qapp,
    tmp_path: Path,
):
    engine = TaskObservationEngine(
        tmp_path,
    )

    sessions = []

    for index in range(3):
        session = engine.start(
            f"filesystem.task.{index}",
        )

        snapshot = session.finish()

        sessions.append(
            snapshot,
        )

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget.refresh_history()

        assert widget.history_list.count() == 3

        ids = {
            widget.history_list.item(index).text()
            for index in range(
                widget.history_list.count(),
            )
        }

        expected_ids = {snapshot.identity.session_id for snapshot in sessions}

        assert ids == expected_ids

    finally:
        widget.bridge.close()


def test_observation_widget_feature_selection_changes_plot(
    qapp,
    tmp_path: Path,
):
    engine = TaskObservationEngine(
        tmp_path,
    )

    session = engine.start(
        "filesystem",
    )

    session.continuous.record(
        "row_count",
        10,
    )

    session.continuous.record(
        "row_count",
        20,
    )

    session.continuous.record(
        "duration",
        1.5,
    )

    snapshot = session.finish()

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget._display_snapshot(
            snapshot,
        )

        widget.feature_selector.setCurrentText(
            "row_count",
        )

        assert widget.plot._title == "row_count"
        assert widget.plot._values == [
            10.0,
            20.0,
        ]

        widget.feature_selector.setCurrentText(
            "duration",
        )

        assert widget.plot._title == "duration"
        assert widget.plot._values == [
            1.5,
        ]

    finally:
        widget.bridge.close()


# ============================================================================
# ObservationWidget helpers
# ============================================================================


def test_observation_widget_safe_text():
    assert ObservationWidget._safe_text(None) == "<missing>"
    assert ObservationWidget._safe_text("hello") == "hello"
    assert ObservationWidget._safe_text(123) == "123"


# ============================================================================
# End-to-end persisted observation path
# ============================================================================


def test_qt_worker_to_storage_to_replay_to_widget(
    qapp,
    tmp_path: Path,
):
    worker = ObservationWorker(
        str(tmp_path),
    )

    finished = []

    worker.task_finished.connect(
        finished.append,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_event(
        "tool_started",
        {
            "tool_name": "read_table",
            "path": "Employees.csv",
        },
    )

    worker.record_event(
        "tool_completed",
        {
            "tool_name": "read_table",
            "path": "Employees.csv",
            "success": True,
        },
    )

    worker.finish_task()

    assert len(finished) == 1

    produced = finished[0]

    worker.shutdown()

    replay = ReplayAPI(
        tmp_path,
    )

    loaded = replay.session(
        produced.identity.session_id,
    )

    assert loaded.identity.session_id == produced.identity.session_id

    assert loaded.status == "completed"

    continuous = {item.name: item.value for item in loaded.continuous}

    assert continuous["total_tool_calls"] == 1.0
    assert continuous["successful_tool_calls"] == 1.0
    assert continuous["failed_tool_calls"] == 0.0
    assert continuous["read_table_count"] == 1.0
    assert continuous["file_access_count"] == 1.0

    widget = ObservationWidget(
        tmp_path,
    )

    try:
        widget.refresh_history()

        assert widget.history_list.count() == 1

        item = widget.history_list.item(
            0,
        )

        widget._load_history_item(
            item,
        )

        assert widget._snapshot is not None

        assert widget._snapshot.identity.session_id == produced.identity.session_id

        assert widget.session_status_label.text() == "completed"

        feature_names = [
            widget.feature_selector.itemText(index)
            for index in range(
                widget.feature_selector.count(),
            )
        ]

        assert "total_tool_calls" in feature_names
        assert "read_table_count" in feature_names

    finally:
        widget.bridge.close()
