from __future__ import annotations

from pathlib import Path
import sqlite3

from .connection import SQLiteConnection
from .repository import SQLiteRepository
from .schema import create_schema
from .migrations import migrate


class SQLiteObservationStore:
    """
    Transactional persistent store for the observation engine.

    One store owns one SQLite database file.
    """

    def __init__(
        self,
        database_path: str | Path,
    ):
        self.database_path = Path(database_path)

        self._database = SQLiteConnection(self.database_path)

        self._connection: sqlite3.Connection | None = None
        self._repository: SQLiteRepository | None = None

    def open(self) -> None:
        if self._connection is not None:
            return

        connection = self._database.connect()

        create_schema(connection)
        migrate(connection)

        self._connection = connection
        self._repository = SQLiteRepository(connection)

    def close(self) -> None:
        if self._connection is None:
            return

        self._connection.close()

        self._connection = None
        self._repository = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def repository(self) -> SQLiteRepository:
        self.open()

        assert self._repository is not None

        return self._repository

    def transaction(self):
        self.open()

        assert self._connection is not None

        return self._connection

    def commit(self) -> None:
        if self._connection is not None:
            self._connection.commit()

    def rollback(self) -> None:
        if self._connection is not None:
            self._connection.rollback()
