from __future__ import annotations

from typing import Any, Iterable


class TableFormatter:
    """UI-neutral helpers for rendering table-like filesystem results."""

    @staticmethod
    def columns(rows: Iterable[dict[str, Any]]) -> list[str]:
        rows = list(rows)
        columns: list[str] = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    columns.append(str(key))
        return columns

    @staticmethod
    def normalized_rows(rows: Iterable[Any]) -> tuple[list[str], list[list[str]]]:
        rows = list(rows)
        if not rows:
            return [], []

        if all(isinstance(row, dict) for row in rows):
            columns = TableFormatter.columns(rows)
            matrix = [
                ["" if row.get(column) is None else str(row.get(column)) for column in columns]
                for row in rows
            ]
            return columns, matrix

        if all(isinstance(row, (list, tuple)) for row in rows):
            width = max(len(row) for row in rows)
            columns = [f"Column {i + 1}" for i in range(width)]
            matrix = [
                ["" if i >= len(row) or row[i] is None else str(row[i]) for i in range(width)]
                for row in rows
            ]
            return columns, matrix

        return ["Value"], [[str(row)] for row in rows]
