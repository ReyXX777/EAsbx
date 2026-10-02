from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

from .models import ObservationSnapshot


class SessionStore:
    """Append-oriented JSONL persistence for completed observation sessions."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def save(self, snapshot: ObservationSnapshot) -> Path:
        path = self.root / f"{snapshot.identity.session_id}.json"
        payload = snapshot_to_dict(snapshot)
        temporary = path.with_suffix(".json.tmp")
        with self._lock:
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, path)
        return path

    def load(self, session_id: str) -> ObservationSnapshot:
        path = self.root / f"{session_id}.json"
        return snapshot_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_session_ids(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.json"))

    def replay(self, session_id: str) -> ObservationSnapshot:
        return self.load(session_id)


def snapshot_to_dict(snapshot: ObservationSnapshot) -> dict[str, Any]:
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
            {**item.__dict__, "payload": dict(item.payload)}
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


def snapshot_from_dict(data: dict[str, Any]) -> ObservationSnapshot:
    from .models import (
        ContinuousObservation,
        DiscreteObservation,
        TaskEvent,
        TaskIdentity,
        TracePoint,
    )

    identity = TaskIdentity(**data["identity"])
    return ObservationSnapshot(
        identity=identity,
        discrete=tuple(DiscreteObservation(**x) for x in data.get("discrete", [])),
        continuous=tuple(ContinuousObservation(**x) for x in data.get("continuous", [])),
        events=tuple(TaskEvent(**x) for x in data.get("events", [])),
        traces=tuple(TracePoint(**x) for x in data.get("traces", [])),
        started_at=data["started_at"],
        finished_at=data.get("finished_at"),
        status=data.get("status", "unknown"),
        metadata=data.get("metadata", {}),
    )
