from __future__ import annotations

import sqlite3

from .schema import SCHEMA_VERSION


def migrate(connection: sqlite3.Connection) -> None:
    """
    Database migration entry point.

    Stage 6C starts at schema version 1. Future schema changes
    should be added here rather than modifying old migrations.
    """

    row = connection.execute("""
        SELECT value
        FROM schema_metadata
        WHERE key = 'schema_version'
        """).fetchone()

    if row is None:
        return

    current_version = int(row["value"])

    if current_version > SCHEMA_VERSION:
        raise RuntimeError("Database schema is newer than this application.")

    # Future:
    #
    # if current_version < 2:
    #     _migrate_v1_to_v2(connection)
