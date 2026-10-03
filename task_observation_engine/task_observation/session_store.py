from __future__ import annotations

from pathlib import Path

from .models import ObservationSnapshot
from .storage.base import ObservationStorage
from .storage.json_store import JSONObservationStore


class SessionStore(ObservationStorage):
    """Stable storage facade used by the observation engine."""

    def __init__(self, root: str | Path) -> None:
        self._backend = JSONObservationStore(root)

    def save(self, snapshot: ObservationSnapshot):
        return self._backend.save(snapshot)

    def load(self, session_id: str) -> ObservationSnapshot:
        return self._backend.load(session_id)

    def list_session_ids(self) -> list[str]:
        return self._backend.list_session_ids()

    def replay(self, session_id: str) -> ObservationSnapshot:
        return self._backend.replay(session_id)

    def close(self) -> None:
        self._backend.close()
