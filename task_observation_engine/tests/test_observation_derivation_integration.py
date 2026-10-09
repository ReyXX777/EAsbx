from __future__ import annotations

from pathlib import Path

from task_observation import ReplayAPI, TaskObservationEngine


def test_engine_derives_features_on_session_finish(tmp_path: Path) -> None:
    engine = TaskObservationEngine(tmp_path)

    session = engine.start(
        "filesystem",
        metadata={
            "agent_type": "filesystem",
        },
    )

    session.events.event(
        "task_started",
        source="filesystem_worker",
    )

    session.events.event(
        "tool_started",
        source="filesystem_worker",
        payload={
            "tool_name": "list_directory",
            "path": ".",
        },
    )

    session.events.event(
        "tool_completed",
        source="filesystem_worker",
        payload={
            "tool_name": "list_directory",
            "path": ".",
            "success": True,
        },
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

    session.events.event(
        "tool_started",
        source="filesystem_worker",
        payload={
            "tool_name": "read_table",
            "path": "Level_1/Employees.csv",
        },
    )

    session.events.event(
        "tool_completed",
        source="filesystem_worker",
        payload={
            "tool_name": "read_table",
            "path": "Level_1/Employees.csv",
            "success": True,
        },
    )

    session.events.event(
        "tool_started",
        source="filesystem_worker",
        payload={
            "tool_name": "compute_sum",
            "path": None,
        },
    )

    session.events.event(
        "tool_completed",
        source="filesystem_worker",
        payload={
            "tool_name": "compute_sum",
            "path": None,
            "success": True,
        },
    )

    session.events.event(
        "task_completed",
        source="filesystem_worker",
        payload={
            "status": "completed",
        },
    )

    session.events.trace(
        "tool_started",
        action="list_directory",
        path=".",
        discrete={
            "tool_name": "list_directory",
        },
    )

    session.events.trace(
        "tool_completed",
        action="list_directory",
        path=".",
        discrete={
            "success": True,
        },
    )

    session.events.trace(
        "tool_started",
        action="search_files",
        path=".",
        discrete={
            "tool_name": "search_files",
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

    session.events.trace(
        "tool_started",
        action="read_table",
        path="Level_1/Employees.csv",
        discrete={
            "tool_name": "read_table",
        },
    )

    session.events.trace(
        "tool_completed",
        action="read_table",
        path="Level_1/Employees.csv",
        discrete={
            "success": True,
        },
    )

    session.events.trace(
        "tool_started",
        action="compute_sum",
        path=None,
        discrete={
            "tool_name": "compute_sum",
        },
    )

    session.events.trace(
        "tool_completed",
        action="compute_sum",
        path=None,
        discrete={
            "success": True,
        },
    )

    snapshot = session.finish()





    assert len(snapshot.events) > 0
    assert len(snapshot.traces) == 8






    continuous = {item.name: item.value for item in snapshot.continuous}

    assert continuous["total_tool_calls"] == 4.0
    assert continuous["successful_tool_calls"] == 4.0
    assert continuous["failed_tool_calls"] == 0.0
    assert continuous["unique_tools"] == 4.0

    assert continuous["list_directory_count"] == 1.0
    assert continuous["search_files_count"] == 1.0
    assert continuous["read_table_count"] == 1.0
    assert continuous["compute_count"] == 1.0

    assert continuous["unique_paths"] == 2.0
    assert continuous["paths_visited"] == 6.0
    assert continuous["directory_navigation_count"] == 1.0
    assert continuous["file_access_count"] == 1.0
    assert continuous["search_count"] == 1.0





    discrete = {item.name: item.value for item in snapshot.discrete}

    assert discrete["task_status"] == "completed"
    assert discrete["task_completed"] is True
    assert discrete["task_failed"] is False
    assert discrete["task_cancelled"] is False

    assert discrete["had_tool_failure"] is False
    assert discrete["recovered_from_failure"] is False

    assert discrete["used_search"] is True
    assert discrete["used_computation"] is True
    assert discrete["used_file_read"] is True


def test_derived_features_are_persisted_and_replayable(
    tmp_path: Path,
) -> None:
    engine = TaskObservationEngine(tmp_path)

    session = engine.start("filesystem")

    session.events.event(
        "tool_started",
        source="filesystem_worker",
        payload={
            "tool_name": "read_table",
            "path": "Employees.csv",
        },
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

    session.events.trace(
        "tool_started",
        action="read_table",
        path="Employees.csv",
        discrete={
            "tool_name": "read_table",
        },
    )

    session.events.trace(
        "tool_completed",
        action="read_table",
        path="Employees.csv",
        discrete={
            "success": True,
        },
    )

    snapshot = session.finish()





    replay = ReplayAPI(tmp_path)

    loaded = replay.session(
        snapshot.identity.session_id,
    )





    continuous = {item.name: item.value for item in loaded.continuous}

    assert continuous["total_tool_calls"] == 1.0
    assert continuous["successful_tool_calls"] == 1.0
    assert continuous["failed_tool_calls"] == 0.0
    assert continuous["read_table_count"] == 1.0
    assert continuous["file_access_count"] == 1.0

    discrete = {item.name: item.value for item in loaded.discrete}

    assert discrete["task_status"] == "completed"
    assert discrete["task_completed"] is True
    assert discrete["used_file_read"] is True


def test_replay_feature_rows_include_derived_features(
    tmp_path: Path,
) -> None:
    engine = TaskObservationEngine(tmp_path)

    session = engine.start("filesystem")

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

    session.events.trace(
        "tool_started",
        action="search_files",
        path=".",
        discrete={
            "tool_name": "search_files",
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

    replay = ReplayAPI(tmp_path)

    rows = replay.feature_rows(
        [snapshot.identity.session_id],
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["session_id"] == snapshot.identity.session_id
    assert row["family_key"] == "filesystem"
    assert row["status"] == "completed"

    assert row["continuous.total_tool_calls"] == 1.0
    assert row["continuous.successful_tool_calls"] == 1.0
    assert row["continuous.failed_tool_calls"] == 0.0
    assert row["continuous.search_files_count"] == 1.0

    assert row["discrete.task_status"] == "completed"
    assert row["discrete.task_completed"] is True
    assert row["discrete.used_search"] is True
