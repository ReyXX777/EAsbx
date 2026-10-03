from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteConnection:
    """
    Owns SQLite connection configuration.

    SQLite is deliberately kept behind this small class so the rest
    of the observation engine does not depend on sqlite3 directly.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30.0,
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")

        return connection
