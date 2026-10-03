from __future__ import annotations

from typing import Any

from ..models import ObservationSnapshot


def snapshot_to_dict(
    snapshot: ObservationSnapshot,
) -> dict[str, Any]:
    return {
        "identity": {
            "session_id": snapshot.identity.session_id,
            "family_key": snapshot.identity.family_key,
            "task_key": snapshot.identity.task_key,
            "started_at": snapshot.identity.started_at,
        },
        "started_at": snapshot.started_at,
        "finished_at": snapshot.finished_at,
        "status": snapshot.status,
        "metadata": dict(snapshot.metadata),
        "discrete": [item.__dict__ for item in snapshot.discrete],
        "continuous": [item.__dict__ for item in snapshot.continuous],
        "events": [
            {
                **item.__dict__,
                "payload": dict(item.payload),
            }
            for item in snapshot.events
        ],
        "traces": [
            {
                **item.__dict__,
                "discrete": dict(item.discrete),
                "continuous": dict(item.continuous),
            }
            for item in snapshot.traces
        ],
    }


def snapshot_from_dict(
    data: dict[str, Any],
) -> ObservationSnapshot:
    from ..models import (
        ContinuousObservation,
        DiscreteObservation,
        TaskEvent,
        TaskIdentity,
        TracePoint,
    )

    identity = TaskIdentity(**data["identity"])

    return ObservationSnapshot(
        identity=identity,
        discrete=tuple(
            DiscreteObservation(**item) for item in data.get("discrete", [])
        ),
        continuous=tuple(
            ContinuousObservation(**item) for item in data.get("continuous", [])
        ),
        events=tuple(TaskEvent(**item) for item in data.get("events", [])),
        traces=tuple(TracePoint(**item) for item in data.get("traces", [])),
        started_at=data["started_at"],
        finished_at=data.get("finished_at"),
        status=data.get("status", "unknown"),
        metadata=data.get("metadata", {}),
    )
