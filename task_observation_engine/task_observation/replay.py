from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import ObservationSnapshot
from .storage import SessionStore


class ReplayAPI:
    """Read-only API for visualization, experiments and mathematical adapters."""

    def __init__(self, root: str | Path) -> None:
        self.store = SessionStore(root)

    def session_ids(self) -> list[str]:
        return self.store.list_session_ids()

    def session(self, session_id: str) -> ObservationSnapshot:
        return self.store.load(session_id)

    def sessions(self, session_ids: Iterable[str] | None = None) -> list[ObservationSnapshot]:
        ids = list(session_ids) if session_ids is not None else self.session_ids()
        return [self.session(session_id) for session_id in ids]

    def feature_rows(self, session_ids: Iterable[str] | None = None) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for snapshot in self.sessions(session_ids):
            row: dict[str, object] = {
                "session_id": snapshot.identity.session_id,
                "family_key": snapshot.identity.family_key,
                "status": snapshot.status,
            }
            for item in snapshot.discrete:
                row[f"discrete.{item.name}"] = item.value
            for item in snapshot.continuous:
                if item.value is not None:
                    row[f"continuous.{item.name}"] = item.value
            rows.append(row)
        return rows
