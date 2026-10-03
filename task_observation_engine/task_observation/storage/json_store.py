from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from ..models import ObservationSnapshot
from .base import ObservationStorage
from .serialization import snapshot_from_dict, snapshot_to_dict


class JSONObservationStore(ObservationStorage):
    """Filesystem-backed JSON observation store.

    This implementation is intentionally simple and useful for:
    - development
    - debugging
    - inspection
    - migration
    - lightweight tests
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def save(self, snapshot: ObservationSnapshot) -> Path:
        path = self.root / f"{snapshot.identity.session_id}.json"
        temporary = path.with_suffix(".json.tmp")

        payload = snapshot_to_dict(snapshot)

        with self._lock:
            temporary.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            os.replace(temporary, path)

        return path

    def load(self, session_id: str) -> ObservationSnapshot:
        path = self.root / f"{session_id}.json"

        payload = json.loads(path.read_text(encoding="utf-8"))

        return snapshot_from_dict(payload)

    def list_session_ids(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))

    def replay(self, session_id: str) -> ObservationSnapshot:
        return self.load(session_id)
