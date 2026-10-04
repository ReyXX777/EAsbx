from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy

from task_observation.models import ObservationSnapshot
from task_observation.qt.observation_thread import ObservationWorker


@pytest.fixture
def qt_core_app():
    app = QCoreApplication.instance()

    if app is None:
        app = QCoreApplication([])

    return app


def test_observation_worker_records_event(
    tmp_path,
    qt_core_app,
) -> None:
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = QSignalSpy(
        worker.worker_error,
    )

    worker.start_task(
        "filesystem",
        metadata={
            "agent_type": "filesystem",
        },
    )

    worker.record_event(
        "tool_started",
        {
            "tool_name": "list_directory",
            "path": ".",
        },
    )

    assert errors.count() == 0

    assert worker._session is not None

    snapshot = worker._session.snapshot()

    assert len(snapshot.events) == 1

    event = snapshot.events[0]

    assert event.name == "tool_started"
    assert event.source == "qt_observation_worker"
    assert event.payload["tool_name"] == "list_directory"
    assert event.payload["path"] == "."


def test_observation_worker_records_discrete_and_continuous(
    tmp_path,
    qt_core_app,
) -> None:
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = QSignalSpy(
        worker.worker_error,
    )

    worker.start_task(
        "filesystem",
    )

    worker.record_discrete(
        "extension",
        ".csv",
    )

    worker.record_continuous(
        "row_count",
        1000,
    )

    assert errors.count() == 0
    assert worker._session is not None

    snapshot = worker._session.snapshot()

    assert snapshot.discrete[0].name == "extension"
    assert snapshot.discrete[0].value == ".csv"

    assert snapshot.continuous[0].name == "row_count"
    assert snapshot.continuous[0].value == 1000.0


def test_observation_worker_finish_produces_derived_snapshot(
    tmp_path,
    qt_core_app,
) -> None:
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = QSignalSpy(
        worker.worker_error,
    )

    finished = QSignalSpy(
        worker.task_finished,
    )

    worker.start_task(
        "filesystem",
        metadata={
            "agent_type": "filesystem",
        },
    )

    worker.record_event(
        "task_started",
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

    worker.record_event(
        "task_completed",
        {
            "status": "completed",
        },
    )

    worker.finish_task()

    assert errors.count() == 0
    assert finished.count() == 1
    assert worker._session is None

    snapshot = finished.at(0)[0]

    assert isinstance(
        snapshot,
        ObservationSnapshot,
    )

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


def test_observation_worker_finish_persists_finished_snapshot(
    tmp_path,
    qt_core_app,
) -> None:
    worker = ObservationWorker(
        str(tmp_path),
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

    from task_observation.replay import ReplayAPI

    replay = ReplayAPI(
        tmp_path,
    )

    session_ids = replay.session_ids()

    assert len(session_ids) == 1

    loaded = replay.session(
        session_ids[0],
    )

    continuous = {item.name: item.value for item in loaded.continuous}

    discrete = {item.name: item.value for item in loaded.discrete}

    assert continuous["total_tool_calls"] == 1.0
    assert continuous["read_table_count"] == 1.0
    assert continuous["file_access_count"] == 1.0

    assert discrete["task_status"] == "completed"
    assert discrete["task_completed"] is True
    assert discrete["used_file_read"] is True


def test_observation_worker_rejects_second_active_task(
    tmp_path,
    qt_core_app,
) -> None:
    worker = ObservationWorker(
        str(tmp_path),
    )

    errors = QSignalSpy(
        worker.worker_error,
    )

    worker.start_task(
        "filesystem",
    )

    worker.start_task(
        "browser",
    )

    assert errors.count() == 1
    assert "another task is active" in errors.at(0)[0]

    worker.shutdown()
