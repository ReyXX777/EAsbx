from __future__ import annotations

from threading import RLock
from typing import Any, Mapping

from .buckets import BucketManager
from .collectors import ContinuousFeatureCollector, DiscreteFeatureCollector, EventTraceCollector
from .models import ObservationSnapshot, TaskIdentity, utc_now_iso
from .storage import SessionStore


class TaskObservationSession:
    """Live observation session owned by a separate observation thread/process."""

    def __init__(self, identity: TaskIdentity, store: SessionStore | None = None, buckets: BucketManager | None = None) -> None:
        self.identity = identity
        self.discrete = DiscreteFeatureCollector()
        self.continuous = ContinuousFeatureCollector()
        self.events = EventTraceCollector()
        self.store = store
        self.buckets = buckets
        self._started_at = identity.started_at
        self._finished_at: str | None = None
        self._status = "running"
        self._metadata: dict[str, Any] = {}
        self._lock = RLock()

    def set_metadata(self, values: Mapping[str, Any]) -> None:
        with self._lock:
            self._metadata.update(values)

    def finish(self, status: str = "completed") -> ObservationSnapshot:
        with self._lock:
            self._finished_at = utc_now_iso()
            self._status = status
            snapshot = self.snapshot()

        if self.buckets is not None:
            self.buckets.add(snapshot)
        if self.store is not None:
            self.store.save(snapshot)
        return snapshot

    def snapshot(self) -> ObservationSnapshot:
        with self._lock:
            return ObservationSnapshot(
                identity=self.identity,
                discrete=self.discrete.snapshot(),
                continuous=self.continuous.snapshot(),
                events=self.events.events(),
                traces=self.events.traces(),
                started_at=self._started_at,
                finished_at=self._finished_at,
                status=self._status,
                metadata=self._metadata,
            )


class TaskObservationEngine:
    """Public facade used by future filesystem/browser adapters."""

    def __init__(self, storage_root: str | None = None) -> None:
        self.store = SessionStore(storage_root) if storage_root else None
        self.buckets = BucketManager()
        self._sessions: dict[str, TaskObservationSession] = {}
        self._lock = RLock()

    def start(self, family_key: str, *, task_key: str = "", metadata: Mapping[str, Any] | None = None) -> TaskObservationSession:
        identity = TaskIdentity.create(family_key, task_key)
        session = TaskObservationSession(identity, self.store, self.buckets)
        if metadata:
            session.set_metadata(metadata)
        with self._lock:
            self._sessions[identity.session_id] = session
        return session

    def get(self, session_id: str) -> TaskObservationSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def finish(self, session_id: str, status: str = "completed") -> ObservationSnapshot | None:
        session = self.get(session_id)
        if session is None:
            return None
        snapshot = session.finish(status)
        with self._lock:
            self._sessions.pop(session_id, None)
        return snapshot

    def replay(self, session_id: str) -> ObservationSnapshot:
        if self.store is None:
            raise RuntimeError("Persistent storage is not configured.")
        return self.store.replay(session_id)
