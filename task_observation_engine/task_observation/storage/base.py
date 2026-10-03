from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models import ObservationSnapshot


class ObservationStorage(ABC):
    """Backend-independent persistence contract.

    Higher-level observation components depend only on this interface.
    Concrete storage technologies must implement it.
    """

    @abstractmethod
    def save(self, snapshot: ObservationSnapshot) -> Path | None:
        """Persist a completed observation snapshot."""
        raise NotImplementedError

    @abstractmethod
    def load(self, session_id: str) -> ObservationSnapshot:
        """Load one persisted observation session."""
        raise NotImplementedError

    @abstractmethod
    def list_session_ids(self) -> list[str]:
        """Return persisted session identifiers."""
        raise NotImplementedError

    def replay(self, session_id: str) -> ObservationSnapshot:
        """Default replay implementation."""
        return self.load(session_id)

    def close(self) -> None:
        """Release backend resources.

        Backends that do not require explicit cleanup may leave this empty.
        """
        return None

    def __enter__(self) -> "ObservationStorage":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
