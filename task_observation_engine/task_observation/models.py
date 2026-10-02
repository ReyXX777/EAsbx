from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import math
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservationKind(str, Enum):
    SESSION_STARTED = "session_started"
    SESSION_FINISHED = "session_finished"
    FEATURE = "feature"
    EVENT = "event"
    TRACE = "trace"
    DECISION = "decision"
    ERROR = "error"


@dataclass(frozen=True)
class TaskIdentity:
    session_id: str
    family_key: str
    task_key: str = ""
    started_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def create(cls, family_key: str, task_key: str = "") -> "TaskIdentity":
        return cls(
            session_id=uuid.uuid4().hex,
            family_key=family_key,
            task_key=task_key,
        )


@dataclass(frozen=True)
class DiscreteObservation:
    name: str
    value: str | int | bool | None
    timestamp: str = field(default_factory=utc_now_iso)
    source: str = "unknown"
    step: int | None = None


@dataclass(frozen=True)
class ContinuousObservation:
    name: str
    value: float | None
    timestamp: str = field(default_factory=utc_now_iso)
    source: str = "unknown"
    step: int | None = None

    def __post_init__(self) -> None:
        if self.value is not None and not math.isfinite(float(self.value)):
            object.__setattr__(self, "value", None)


@dataclass(frozen=True)
class TaskEvent:
    name: str
    timestamp: str = field(default_factory=utc_now_iso)
    source: str = "unknown"
    payload: Mapping[str, Any] = field(default_factory=dict)
    step: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class TracePoint:
    sequence: int
    timestamp: str
    phase: str
    action: str = ""
    path: str | None = None
    discrete: Mapping[str, str | int | bool | None] = field(default_factory=dict)
    continuous: Mapping[str, float | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "discrete", MappingProxyType(dict(self.discrete)))
        object.__setattr__(self, "continuous", MappingProxyType(dict(self.continuous)))


@dataclass(frozen=True)
class ObservationSnapshot:
    identity: TaskIdentity
    discrete: tuple[DiscreteObservation, ...]
    continuous: tuple[ContinuousObservation, ...]
    events: tuple[TaskEvent, ...]
    traces: tuple[TracePoint, ...]
    started_at: str
    finished_at: str | None
    status: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_feature_vector(self, names: tuple[str, ...]) -> tuple[float, ...]:
        latest: dict[str, float] = {}
        for item in self.continuous:
            if item.value is not None:
                latest[item.name] = float(item.value)
        return tuple(latest.get(name, 0.0) for name in names)


@dataclass(frozen=True)
class BucketKey:
    name: str
    value: str


@dataclass
class ObservationBucket:
    key: BucketKey
    count: int = 0
    sessions: list[str] = field(default_factory=list)

    def add(self, session_id: str) -> None:
        self.count += 1
        if session_id not in self.sessions:
            self.sessions.append(session_id)
