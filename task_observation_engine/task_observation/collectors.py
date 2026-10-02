from __future__ import annotations

from threading import Lock
from typing import Any, Mapping
from datetime import datetime, timezone

from .models import ContinuousObservation, DiscreteObservation, TaskEvent, TracePoint


class DiscreteFeatureCollector:
    """Thread-safe collector for categorical/state-like task features."""

    def __init__(self) -> None:
        self._items: list[DiscreteObservation] = []
        self._lock = Lock()

    def record(self, name: str, value: str | int | bool | None, *, source: str = "unknown", step: int | None = None) -> None:
        with self._lock:
            self._items.append(DiscreteObservation(name, value, source=source, step=step))

    def record_many(self, values: Mapping[str, str | int | bool | None], *, source: str = "unknown", step: int | None = None) -> None:
        with self._lock:
            for name, value in values.items():
                self._items.append(DiscreteObservation(name, value, source=source, step=step))

    def snapshot(self) -> tuple[DiscreteObservation, ...]:
        with self._lock:
            return tuple(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


class ContinuousFeatureCollector:
    """Thread-safe collector for numeric task features.

    Missing/invalid numeric values are accepted and represented as None rather
    than terminating the observation process.
    """

    def __init__(self) -> None:
        self._items: list[ContinuousObservation] = []
        self._lock = Lock()

    def record(self, name: str, value: float | int | None, *, source: str = "unknown", step: int | None = None) -> None:
        safe_value: float | None
        try:
            safe_value = None if value is None else float(value)
        except (TypeError, ValueError):
            safe_value = None
        with self._lock:
            self._items.append(ContinuousObservation(name, safe_value, source=source, step=step))

    def record_many(self, values: Mapping[str, float | int | None], *, source: str = "unknown", step: int | None = None) -> None:
        for name, value in values.items():
            self.record(name, value, source=source, step=step)

    def snapshot(self) -> tuple[ContinuousObservation, ...]:
        with self._lock:
            return tuple(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


class EventTraceCollector:
    """Thread-safe event and trace recorder."""

    def __init__(self) -> None:
        self._events: list[TaskEvent] = []
        self._traces: list[TracePoint] = []
        self._lock = Lock()

    def event(self, name: str, *, source: str = "unknown", payload: Mapping[str, Any] | None = None, step: int | None = None) -> None:
        with self._lock:
            self._events.append(TaskEvent(name=name, source=source, payload=payload or {}, step=step))

    def trace(
        self,
        phase: str,
        *,
        action: str = "",
        path: str | None = None,
        discrete: Mapping[str, str | int | bool | None] | None = None,
        continuous: Mapping[str, float | None] | None = None,
    ) -> int:
        with self._lock:
            sequence = len(self._traces)
            self._traces.append(
                TracePoint(
                    sequence=sequence,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    phase=phase,
                    action=action,
                    path=path,
                    discrete=discrete or {},
                    continuous=continuous or {},
                )
            )
            return sequence

    def events(self) -> tuple[TaskEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def traces(self) -> tuple[TracePoint, ...]:
        with self._lock:
            return tuple(self._traces)
