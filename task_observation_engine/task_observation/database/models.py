from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatabaseSession:
    session_id: str
    task_family: str
    started_at: str
    finished_at: str | None
    status: str


@dataclass(frozen=True)
class DatabaseObservation:
    session_id: str
    sequence: int
    timestamp: str
    name: str
    kind: str
    value: Any


@dataclass(frozen=True)
class DatabaseEvent:
    session_id: str
    sequence: int
    timestamp: str
    event_type: str
    payload: Any


@dataclass(frozen=True)
class DatabaseTracePoint:
    session_id: str
    sequence: int
    timestamp: str
    name: str
    x: float | None
    y: float | None
    z: float | None
    metadata: Any


@dataclass(frozen=True)
class DatabaseLabel:
    session_id: str
    label: str
    source: str
    timestamp: str
