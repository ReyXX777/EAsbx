from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Iterable

from .models import BucketKey, ObservationBucket, ObservationSnapshot


class BucketManager:
    """Groups sessions by stable categorical features without altering raw data."""

    def __init__(self) -> None:
        self._buckets: dict[BucketKey, ObservationBucket] = {}
        self._lock = Lock()

    def add(self, snapshot: ObservationSnapshot) -> None:
        session_id = snapshot.identity.session_id
        values: dict[str, set[str]] = defaultdict(set)
        for item in snapshot.discrete:
            values[item.name].add(self._normalize(item.value))

        with self._lock:
            for name, bucket_values in values.items():
                for value in bucket_values:
                    key = BucketKey(name, value)
                    bucket = self._buckets.setdefault(key, ObservationBucket(key))
                    bucket.add(session_id)

    def get(self, name: str, value: object) -> ObservationBucket | None:
        with self._lock:
            bucket = self._buckets.get(BucketKey(name, self._normalize(value)))
            if bucket is None:
                return None
            return ObservationBucket(bucket.key, bucket.count, list(bucket.sessions))

    def all(self) -> tuple[ObservationBucket, ...]:
        with self._lock:
            return tuple(ObservationBucket(b.key, b.count, list(b.sessions)) for b in self._buckets.values())

    @staticmethod
    def _normalize(value: object) -> str:
        return "<MISSING>" if value is None else str(value)
