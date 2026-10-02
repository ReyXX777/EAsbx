from __future__ import annotations

import math
from typing import Any, Iterable


class TableOperationError(RuntimeError):
    """Raised when a table computation cannot be performed."""


class TableOperations:
    """
    Deterministic operations over structured table data.

    This class performs computation locally and does not know
    anything about Gemini, Qt, filesystem paths, or UI rendering.
    """

    @staticmethod
    def _numeric_values(
        values: Iterable[Any],
    ) -> list[int | float]:
        """
        Convert supplied values into numeric values.

        Integer and floating-point values are accepted directly.
        Numeric strings are also accepted so CSV-derived values
        can be processed without requiring the caller to manually
        convert every field.
        """

        numeric_values: list[int | float] = []

        for value in values:
            if isinstance(value, bool):
                raise TableOperationError(
                    "Boolean values are not valid numeric values."
                )

            if isinstance(value, (int, float)):
                number = value

            elif isinstance(value, str):
                stripped = value.strip()

                if not stripped:
                    raise TableOperationError(
                        "Empty values cannot be used in numeric calculations."
                    )

                try:
                    number = float(stripped)

                    if number.is_integer():
                        number = int(number)

                except ValueError as exc:
                    raise TableOperationError(
                        f"Value is not numeric: {value!r}"
                    ) from exc

            else:
                raise TableOperationError(f"Unsupported numeric value: {value!r}")

            if isinstance(number, float) and not math.isfinite(number):
                raise TableOperationError("Non-finite numbers are not allowed.")

            numeric_values.append(number)

        return numeric_values

    @classmethod
    def sum(
        cls,
        values: Iterable[Any],
    ) -> int | float:
        """Return the sum of numeric values."""

        numeric_values = cls._numeric_values(values)

        if not numeric_values:
            raise TableOperationError("Cannot calculate sum of an empty collection.")

        return sum(numeric_values)

    @classmethod
    def average(
        cls,
        values: Iterable[Any],
    ) -> int | float:
        """Return the arithmetic mean of numeric values."""

        numeric_values = cls._numeric_values(values)

        if not numeric_values:
            raise TableOperationError(
                "Cannot calculate average of an empty collection."
            )

        return sum(numeric_values) / len(numeric_values)

    @classmethod
    def minimum(
        cls,
        values: Iterable[Any],
    ) -> int | float:
        """Return the smallest numeric value."""

        numeric_values = cls._numeric_values(values)

        if not numeric_values:
            raise TableOperationError(
                "Cannot calculate minimum of an empty collection."
            )

        return min(numeric_values)

    @classmethod
    def maximum(
        cls,
        values: Iterable[Any],
    ) -> int | float:
        """Return the largest numeric value."""

        numeric_values = cls._numeric_values(values)

        if not numeric_values:
            raise TableOperationError(
                "Cannot calculate maximum of an empty collection."
            )

        return max(numeric_values)

    @staticmethod
    def count(
        values: Iterable[Any],
    ) -> int:
        """Return the number of supplied values."""

        return sum(1 for _ in values)
