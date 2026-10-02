from pathlib import Path

from task_observation import ReplayAPI, TaskObservationEngine, generate_runs


def test_missing_values_do_not_stop_collection(tmp_path: Path) -> None:
    engine = TaskObservationEngine(tmp_path)
    session = engine.start("demo.family")
    session.discrete.record("optional", None)
    session.continuous.record("optional_number", None)
    session.continuous.record("bad_number", "not-a-number")
    snapshot = session.finish()

    assert snapshot.status == "completed"
    assert len(snapshot.discrete) == 1
    assert len(snapshot.continuous) == 2
    assert snapshot.continuous[-1].value is None


def test_persistence_and_replay(tmp_path: Path) -> None:
    engine = TaskObservationEngine(tmp_path)
    session = engine.start("filesystem.read_table.calculate")
    session.continuous.record("row_count", 1000)
    session.discrete.record("extension", ".csv")
    snapshot = session.finish()

    replay = ReplayAPI(tmp_path)
    loaded = replay.session(snapshot.identity.session_id)
    assert loaded.identity.session_id == snapshot.identity.session_id
    assert loaded.continuous[0].value == 1000.0
    assert loaded.discrete[0].value == ".csv"


def test_simulation_produces_multiple_replayable_runs(tmp_path: Path) -> None:
    snapshots = generate_runs(tmp_path, count=5, seed=42)
    assert len(snapshots) == 5
    replay = ReplayAPI(tmp_path)
    assert len(replay.session_ids()) == 5
    assert len(replay.feature_rows()) == 5
