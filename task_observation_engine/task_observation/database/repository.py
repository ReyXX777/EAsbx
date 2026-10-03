from __future__ import annotations

import json
from typing import Any

from .models import (
    DatabaseEvent,
    DatabaseLabel,
    DatabaseObservation,
    DatabaseSession,
    DatabaseTracePoint,
)


def _encode_value(
    value: Any,
) -> tuple[str | None, float | None, str | None, str | None]:
    if value is None:
        return None, None, None, None

    if isinstance(value, bool):
        return "bool", None, str(value), None

    if isinstance(value, (int, float)):
        return "number", float(value), None, None

    if isinstance(value, str):
        return "text", None, value, None

    try:
        return (
            "json",
            None,
            None,
            json.dumps(
                value,
                ensure_ascii=False,
            ),
        )
    except (TypeError, ValueError):
        return "text", None, str(value), None


def _decode_value(
    value_type: str | None,
    numeric_value: float | None,
    text_value: str | None,
    json_value: str | None,
) -> Any:

    if value_type is None:
        return None

    if value_type == "number":
        return numeric_value

    if value_type == "text":
        return text_value

    if value_type == "bool":
        return text_value == "True"

    if value_type == "json":
        if json_value is None:
            return None
        return json.loads(json_value)

    return text_value


class SQLiteRepository:
    """
    Low-level SQLite repository.

    This class knows SQLite tables, but does not know anything
    about filesystem agents, browser agents, or Qt.
    """

    def __init__(self, connection):
        self.connection = connection

    def create_session(
        self,
        session_id: str,
        task_family: str,
        started_at: str,
        status: str,
    ) -> None:

        self.connection.execute(
            """
            INSERT INTO sessions(
                session_id,
                task_family,
                started_at,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                task_family,
                started_at,
                status,
            ),
        )

    def finish_session(
        self,
        session_id: str,
        finished_at: str,
        status: str,
    ) -> None:

        self.connection.execute(
            """
            UPDATE sessions
            SET
                finished_at = ?,
                status = ?
            WHERE session_id = ?
            """,
            (
                finished_at,
                status,
                session_id,
            ),
        )

    def insert_observation(
        self,
        session_id: str,
        sequence: int,
        timestamp: str,
        name: str,
        kind: str,
        value: Any,
    ) -> None:

        (
            value_type,
            numeric_value,
            text_value,
            json_value,
        ) = _encode_value(value)

        self.connection.execute(
            """
            INSERT INTO observations(
                session_id,
                sequence,
                timestamp,
                name,
                kind,
                value_type,
                numeric_value,
                text_value,
                json_value
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                sequence,
                timestamp,
                name,
                kind,
                value_type,
                numeric_value,
                text_value,
                json_value,
            ),
        )

    def insert_event(
        self,
        session_id: str,
        sequence: int,
        timestamp: str,
        event_type: str,
        payload: Any,
    ) -> None:

        payload_json = None

        if payload is not None:
            payload_json = json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            )

        self.connection.execute(
            """
            INSERT INTO events(
                session_id,
                sequence,
                timestamp,
                event_type,
                payload
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                sequence,
                timestamp,
                event_type,
                payload_json,
            ),
        )

    def insert_trace_point(
        self,
        session_id: str,
        sequence: int,
        timestamp: str,
        name: str,
        x: float | None,
        y: float | None,
        z: float | None,
        metadata: Any,
    ) -> None:

        metadata_json = None

        if metadata is not None:
            metadata_json = json.dumps(
                metadata,
                ensure_ascii=False,
                default=str,
            )

        self.connection.execute(
            """
            INSERT INTO trace_points(
                session_id,
                sequence,
                timestamp,
                name,
                x,
                y,
                z,
                metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                sequence,
                timestamp,
                name,
                x,
                y,
                z,
                metadata_json,
            ),
        )

    def insert_label(
        self,
        session_id: str,
        label: str,
        source: str,
        timestamp: str,
    ) -> None:

        self.connection.execute(
            """
            INSERT INTO labels(
                session_id,
                label,
                source,
                timestamp
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                label,
                source,
                timestamp,
            ),
        )

    def get_session(
        self,
        session_id: str,
    ) -> DatabaseSession | None:

        row = self.connection.execute(
            """
            SELECT
                session_id,
                task_family,
                started_at,
                finished_at,
                status
            FROM sessions
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()

        if row is None:
            return None

        return DatabaseSession(
            session_id=row["session_id"],
            task_family=row["task_family"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            status=row["status"],
        )

    def list_session_ids(self) -> list[str]:

        rows = self.connection.execute("""
            SELECT session_id
            FROM sessions
            ORDER BY started_at
            """).fetchall()

        return [row["session_id"] for row in rows]

    def observations(
        self,
        session_id: str,
    ) -> list[DatabaseObservation]:

        rows = self.connection.execute(
            """
            SELECT
                session_id,
                sequence,
                timestamp,
                name,
                kind,
                value_type,
                numeric_value,
                text_value,
                json_value
            FROM observations
            WHERE session_id = ?
            ORDER BY sequence, id
            """,
            (session_id,),
        ).fetchall()

        return [
            DatabaseObservation(
                session_id=row["session_id"],
                sequence=row["sequence"],
                timestamp=row["timestamp"],
                name=row["name"],
                kind=row["kind"],
                value=_decode_value(
                    row["value_type"],
                    row["numeric_value"],
                    row["text_value"],
                    row["json_value"],
                ),
            )
            for row in rows
        ]

    def events(
        self,
        session_id: str,
    ) -> list[DatabaseEvent]:

        rows = self.connection.execute(
            """
            SELECT
                session_id,
                sequence,
                timestamp,
                event_type,
                payload
            FROM events
            WHERE session_id = ?
            ORDER BY sequence, id
            """,
            (session_id,),
        ).fetchall()

        return [
            DatabaseEvent(
                session_id=row["session_id"],
                sequence=row["sequence"],
                timestamp=row["timestamp"],
                event_type=row["event_type"],
                payload=(
                    json.loads(row["payload"]) if row["payload"] is not None else None
                ),
            )
            for row in rows
        ]

    def trace_points(
        self,
        session_id: str,
    ) -> list[DatabaseTracePoint]:

        rows = self.connection.execute(
            """
            SELECT
                session_id,
                sequence,
                timestamp,
                name,
                x,
                y,
                z,
                metadata
            FROM trace_points
            WHERE session_id = ?
            ORDER BY sequence, id
            """,
            (session_id,),
        ).fetchall()

        return [
            DatabaseTracePoint(
                session_id=row["session_id"],
                sequence=row["sequence"],
                timestamp=row["timestamp"],
                name=row["name"],
                x=row["x"],
                y=row["y"],
                z=row["z"],
                metadata=(
                    json.loads(row["metadata"]) if row["metadata"] is not None else None
                ),
            )
            for row in rows
        ]

    def labels(
        self,
        session_id: str,
    ) -> list[DatabaseLabel]:

        rows = self.connection.execute(
            """
            SELECT
                session_id,
                label,
                source,
                timestamp
            FROM labels
            WHERE session_id = ?
            ORDER BY timestamp, id
            """,
            (session_id,),
        ).fetchall()

        return [
            DatabaseLabel(
                session_id=row["session_id"],
                label=row["label"],
                source=row["source"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
