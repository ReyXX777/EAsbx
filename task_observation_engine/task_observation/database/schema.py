from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    task_family TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id TEXT NOT NULL,

    sequence INTEGER NOT NULL,
    timestamp TEXT NOT NULL,

    name TEXT NOT NULL,
    kind TEXT NOT NULL,

    value_type TEXT,
    numeric_value REAL,
    text_value TEXT,
    json_value TEXT,

    FOREIGN KEY(session_id)
        REFERENCES sessions(session_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id TEXT NOT NULL,

    sequence INTEGER NOT NULL,
    timestamp TEXT NOT NULL,

    event_type TEXT NOT NULL,
    payload TEXT,

    FOREIGN KEY(session_id)
        REFERENCES sessions(session_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trace_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id TEXT NOT NULL,

    sequence INTEGER NOT NULL,
    timestamp TEXT NOT NULL,

    name TEXT NOT NULL,

    x REAL,
    y REAL,
    z REAL,

    metadata TEXT,

    FOREIGN KEY(session_id)
        REFERENCES sessions(session_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id TEXT NOT NULL,

    label TEXT NOT NULL,
    source TEXT NOT NULL,
    timestamp TEXT NOT NULL,

    FOREIGN KEY(session_id)
        REFERENCES sessions(session_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_observations_session
ON observations(session_id);

CREATE INDEX IF NOT EXISTS idx_observations_name
ON observations(name);

CREATE INDEX IF NOT EXISTS idx_observations_kind
ON observations(kind);

CREATE INDEX IF NOT EXISTS idx_events_session
ON events(session_id);

CREATE INDEX IF NOT EXISTS idx_trace_session
ON trace_points(session_id);

CREATE INDEX IF NOT EXISTS idx_labels_session
ON labels(session_id);
"""


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)

    connection.execute(
        """
        INSERT OR IGNORE INTO schema_metadata(key, value)
        VALUES ('schema_version', ?)
        """,
        (str(SCHEMA_VERSION),),
    )

    connection.commit()
