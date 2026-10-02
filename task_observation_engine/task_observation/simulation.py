from __future__ import annotations

import random
from pathlib import Path

from .models import ObservationSnapshot
from .session import TaskObservationEngine


def generate_runs(root: str | Path, *, count: int = 10, seed: int = 7) -> list[ObservationSnapshot]:
    """Produce deterministic task traces for Stage 6 development and replay tests."""
    rng = random.Random(seed)
    engine = TaskObservationEngine(str(root))
    snapshots: list[ObservationSnapshot] = []

    for index in range(count):
        session = engine.start(
            "filesystem.read_table.calculate",
            task_key="employees.csv",
            metadata={"producer": "stage6-simulation", "run": index + 1},
        )
        session.events.event("task_started", source="simulation")
        session.discrete.record("operation_family", "read_table_calculate", source="simulation")
        session.discrete.record("extension", ".csv", source="simulation")
        session.discrete.record("approval_label", True if index < max(1, count - 2) else False, source="simulation")

        rows = 100 + index * 25
        elapsed = max(0.01, rng.gauss(1.0, 0.1))
        session.continuous.record("row_count", rows, source="simulation")
        session.continuous.record("elapsed_seconds", elapsed, source="simulation")
        session.continuous.record("numeric_column_count", 1, source="simulation")

        session.events.trace(
            "read",
            action="read_table",
            path="Level_1/Level_2/Level_3/Employees.csv",
            discrete={"extension": ".csv"},
            continuous={"row_count": float(rows)},
        )
        session.events.trace(
            "calculate",
            action="calculate",
            continuous={"elapsed_seconds": elapsed},
        )
        session.events.event("task_finished", source="simulation", payload={"success": True})
        snapshots.append(session.finish("completed"))

    return snapshots
