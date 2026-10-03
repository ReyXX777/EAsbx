from __future__ import annotations

from task_observation.models import (
    ContinuousObservation,
    DiscreteObservation,
    ObservationSnapshot,
    TaskEvent,
    TaskIdentity,
    TracePoint,
)
from task_observation.observation import (
    FeatureDeriver,
    NavigationObserver,
    OutcomeObserver,
    TimingObserver,
    ToolObserver,
)


def make_snapshot() -> ObservationSnapshot:
    identity = TaskIdentity(
        session_id="test-session",
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
                name="approval_label",
                value=True,
            ),
        ),
        continuous=(),
        events=(
            TaskEvent(
                name="task_started",
                timestamp="2026-10-03T13:03:33+00:00",
                source="filesystem_worker",
            ),
            TaskEvent(
                name="tool_started",
                timestamp="2026-10-03T13:03:34+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "list_directory",
                    "path": ".",
                },
            ),
            TaskEvent(
                name="tool_completed",
                timestamp="2026-10-03T13:03:35+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "list_directory",
                    "path": ".",
                    "success": True,
                },
            ),
            TaskEvent(
                name="tool_started",
                timestamp="2026-10-03T13:03:36+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "search_files",
                    "path": ".",
                },
            ),
            TaskEvent(
                name="tool_completed",
                timestamp="2026-10-03T13:03:37+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "search_files",
                    "path": ".",
                    "success": True,
                },
            ),
            TaskEvent(
                name="tool_started",
                timestamp="2026-10-03T13:03:38+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "read_table",
                    "path": "Level_1/Level_2/Employees.csv",
                },
            ),
            TaskEvent(
                name="tool_completed",
                timestamp="2026-10-03T13:03:39+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "read_table",
                    "path": "Level_1/Level_2/Employees.csv",
                    "success": True,
                },
            ),
            TaskEvent(
                name="tool_started",
                timestamp="2026-10-03T13:03:40+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "compute_sum",
                    "path": None,
                },
            ),
            TaskEvent(
                name="tool_completed",
                timestamp="2026-10-03T13:03:41+00:00",
                source="filesystem_worker",
                payload={
                    "tool_name": "compute_sum",
                    "path": None,
                    "success": True,
                },
            ),
            TaskEvent(
                name="task_completed",
                timestamp="2026-10-03T13:03:43+00:00",
                source="filesystem_worker",
                payload={
                    "status": "completed",
                },
            ),
        ),
        traces=(
            TracePoint(
                sequence=0,
                timestamp="2026-10-03T13:03:34+00:00",
                phase="tool_started",
                action="list_directory",
                path=".",
                discrete={
                    "tool_name": "list_directory",
                },
            ),
            TracePoint(
                sequence=1,
                timestamp="2026-10-03T13:03:35+00:00",
                phase="tool_completed",
                action="list_directory",
                path=".",
                discrete={
                    "success": True,
                },
            ),
            TracePoint(
                sequence=2,
                timestamp="2026-10-03T13:03:36+00:00",
                phase="tool_started",
                action="search_files",
                path=".",
                discrete={
                    "tool_name": "search_files",
                },
            ),
            TracePoint(
                sequence=3,
                timestamp="2026-10-03T13:03:37+00:00",
                phase="tool_completed",
                action="search_files",
                path=".",
                discrete={
                    "success": True,
                },
            ),
            TracePoint(
                sequence=4,
                timestamp="2026-10-03T13:03:38+00:00",
                phase="tool_started",
                action="read_table",
                path="Level_1/Level_2/Employees.csv",
                discrete={
                    "tool_name": "read_table",
                },
            ),
            TracePoint(
                sequence=5,
                timestamp="2026-10-03T13:03:39+00:00",
                phase="tool_completed",
                action="read_table",
                path="Level_1/Level_2/Employees.csv",
                discrete={
                    "success": True,
                },
            ),
            TracePoint(
                sequence=6,
                timestamp="2026-10-03T13:03:40+00:00",
                phase="tool_started",
                action="compute_sum",
                path=None,
                discrete={
                    "tool_name": "compute_sum",
                },
            ),
            TracePoint(
                sequence=7,
                timestamp="2026-10-03T13:03:41+00:00",
                phase="tool_completed",
                action="compute_sum",
                path=None,
                discrete={
                    "success": True,
                },
            ),
        ),
    )


def test_tool_observer_derives_tool_usage():
    observation = ToolObserver().observe(make_snapshot())

    assert observation.total_tool_calls == 4
    assert observation.successful_tool_calls == 4
    assert observation.failed_tool_calls == 0
    assert observation.unique_tools == 4

    assert observation.list_directory_count == 1
    assert observation.search_files_count == 1
    assert observation.read_table_count == 1
    assert observation.compute_count == 1


def test_navigation_observer_derives_navigation_features():
    observation = NavigationObserver().observe(make_snapshot())

    assert observation.unique_paths == 2
    assert observation.paths_visited == 6
    assert observation.directory_navigation_count == 1
    assert observation.file_access_count == 1
    assert observation.search_count == 1
    assert observation.maximum_path_depth == 3


def test_timing_observer_derives_task_duration():
    observation = TimingObserver().observe(make_snapshot())

    assert observation.task_duration_seconds == 10.0
    assert observation.average_tool_duration_seconds == 1.0
    assert observation.minimum_tool_duration_seconds == 1.0
    assert observation.maximum_tool_duration_seconds == 1.0


def test_outcome_observer_derives_completed_state():
    observation = OutcomeObserver().observe(make_snapshot())

    assert observation.status == "completed"
    assert observation.completed is True
    assert observation.failed is False
    assert observation.cancelled is False
    assert observation.had_tool_failure is False
    assert observation.recovered_from_failure is False
    assert observation.approval_label is True


def test_feature_deriver_combines_all_observers():
    features = FeatureDeriver().derive(make_snapshot())

    continuous = features.continuous_features()
    discrete = features.discrete_features()

    assert continuous["total_tool_calls"] == 4.0
    assert continuous["successful_tool_calls"] == 4.0
    assert continuous["failed_tool_calls"] == 0.0
    assert continuous["compute_count"] == 1.0
    assert continuous["task_duration_seconds"] == 10.0

    assert discrete["task_status"] == "completed"
    assert discrete["task_completed"] is True
    assert discrete["task_failed"] is False
    assert discrete["used_search"] is True
    assert discrete["used_computation"] is True
    assert discrete["used_file_read"] is True
    assert discrete["approval_label"] is True


def test_outcome_observer_detects_recovery():
    snapshot = make_snapshot()

    events = list(snapshot.events)

    events.insert(
        -1,
        TaskEvent(
            name="tool_completed",
            timestamp="2026-10-03T13:03:42+00:00",
            source="filesystem_worker",
            payload={
                "tool_name": "read_file",
                "path": "recovered.txt",
                "success": False,
            },
        ),
    )

    events.insert(
        -1,
        TaskEvent(
            name="tool_completed",
            timestamp="2026-10-03T13:03:42.500000+00:00",
            source="filesystem_worker",
            payload={
                "tool_name": "read_file",
                "path": "recovered.txt",
                "success": True,
            },
        ),
    )

    modified = ObservationSnapshot(
        identity=snapshot.identity,
        discrete=snapshot.discrete,
        continuous=snapshot.continuous,
        events=tuple(events),
        traces=snapshot.traces,
        started_at=snapshot.started_at,
        finished_at=snapshot.finished_at,
        status=snapshot.status,
        metadata=snapshot.metadata,
    )

    observation = OutcomeObserver().observe(modified)

    assert observation.had_tool_failure is True
    assert observation.recovered_from_failure is True
