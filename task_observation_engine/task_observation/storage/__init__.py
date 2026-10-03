"""Storage abstraction for the task observation engine.

The public storage API is exposed here so callers do not need to know
which persistence backend is being used internally.
"""

from .base import ObservationStorage
from .json_store import JSONObservationStore


class SessionStore:
    """Backward-compatible facade over the configured observation store.

    Existing observation-engine code can continue to use:

        from task_observation.storage import SessionStore

    without knowing whether the underlying implementation is JSON,
    SQLite, or another future backend.
    """

    def __init__(self, root: str) -> None:
        self._backend = JSONObservationStore(root)

    def save(self, snapshot):
        return self._backend.save(snapshot)

    def load(self, session_id: str):
        return self._backend.load(session_id)

    def list_session_ids(self) -> list[str]:
        return self._backend.list_session_ids()

    def replay(self, session_id: str):
        return self._backend.replay(session_id)

    def close(self) -> None:
        close = getattr(self._backend, "close", None)
        if close is not None:
            close()


__all__ = [
    "ObservationStorage",
    "JSONObservationStore",
    "SessionStore",
]
