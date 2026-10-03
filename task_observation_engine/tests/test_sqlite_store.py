from pathlib import Path

from task_observation.database import SQLiteObservationStore


def test_database_survives_store_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.sqlite3"

    with SQLiteObservationStore(database_path) as store:
        store.repository.create_session(
            session_id="session-001",
            task_family="filesystem.read_table.calculate",
            started_at="2026-10-03T10:00:00",
            status="running",
        )

        store.repository.insert_observation(
            session_id="session-001",
            sequence=1,
            timestamp="2026-10-03T10:00:01",
            name="row_count",
            kind="continuous",
            value=1000,
        )

        store.repository.insert_observation(
            session_id="session-001",
            sequence=2,
            timestamp="2026-10-03T10:00:02",
            name="optional_value",
            kind="continuous",
            value=None,
        )

        store.repository.insert_observation(
            session_id="session-001",
            sequence=3,
            timestamp="2026-10-03T10:00:03",
            name="extension",
            kind="discrete",
            value=".csv",
        )

        store.repository.insert_event(
            session_id="session-001",
            sequence=4,
            timestamp="2026-10-03T10:00:04",
            event_type="calculate.completed",
            payload={
                "result": 1044000000,
            },
        )

        store.repository.insert_label(
            session_id="session-001",
            label="ALLOW",
            source="human",
            timestamp="2026-10-03T10:00:05",
        )

        store.repository.finish_session(
            session_id="session-001",
            finished_at="2026-10-03T10:00:06",
            status="completed",
        )

        store.commit()

    assert database_path.exists()

    # Simulate completely new application runtime.
    with SQLiteObservationStore(database_path) as store:
        session = store.repository.get_session("session-001")

        assert session is not None
        assert session.status == "completed"

        observations = store.repository.observations("session-001")

        assert len(observations) == 3
        assert observations[0].value == 1000.0
        assert observations[1].value is None
        assert observations[2].value == ".csv"

        events = store.repository.events("session-001")

        assert len(events) == 1
        assert events[0].payload["result"] == 1044000000

        labels = store.repository.labels("session-001")

        assert len(labels) == 1
        assert labels[0].label == "ALLOW"


def test_database_supports_multiple_sessions(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.sqlite3"

    with SQLiteObservationStore(database_path) as store:
        for index in range(5):
            session_id = f"session-{index}"

            store.repository.create_session(
                session_id=session_id,
                task_family="demo.family",
                started_at=f"2026-10-03T10:00:0{index}",
                status="completed",
            )

        store.commit()

    with SQLiteObservationStore(database_path) as store:
        session_ids = store.repository.list_session_ids()

        assert len(session_ids) == 5
        assert "session-0" in session_ids
        assert "session-4" in session_ids
