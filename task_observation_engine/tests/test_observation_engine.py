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

    # ----------------------------------------------------------
    # Raw observations must survive derivation unchanged.
    # ----------------------------------------------------------

    optional = [
        item
        for item in snapshot.discrete
        if item.name == "optional" and item.source == "unknown"
    ]

    assert len(optional) == 1
    assert optional[0].value is None

    optional_number = [
        item
        for item in snapshot.continuous
        if item.name == "optional_number" and item.source == "unknown"
    ]

    assert len(optional_number) == 1
    assert optional_number[0].value is None

    bad_number = [
        item
        for item in snapshot.continuous
        if item.name == "bad_number" and item.source == "unknown"
    ]

    assert len(bad_number) == 1
    assert bad_number[0].value is None

    # ----------------------------------------------------------
    # Derived observations must also have been produced.
    # ----------------------------------------------------------

    assert any(
        item.name == "task_status"
        and item.value == "completed"
        and item.source == "feature_deriver"
        for item in snapshot.discrete
    )

    assert any(
        item.name == "task_completed"
        and item.value is True
        and item.source == "feature_deriver"
        for item in snapshot.discrete
    )

    assert any(
        item.name == "total_tool_calls"
        and item.value == 0.0
        and item.source == "feature_deriver"
        for item in snapshot.continuous
    )


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
