from __future__ import annotations

from typing import Any, Iterable

from .compute_models import (
    ComputeOperation,
    ComputeRequest,
    ComputeResult,
)
from .table_operations import TableOperationError, TableOperations


class ComputeService:
    """
    Public boundary for deterministic local computation.

    This service contains no Gemini, Qt, filesystem, or UI logic.

    Its purpose is to receive structured data and perform
    deterministic computation locally on the machine.
    """

    def __init__(self) -> None:
        self.table_operations = TableOperations()

    def execute(
        self,
        request: ComputeRequest,
    ) -> ComputeResult:
        """
        Execute a compute request.
        """

        try:
            operation = request.operation

            if operation == ComputeOperation.SUM:
                value = self.table_operations.sum(request.values)

            elif operation == ComputeOperation.AVERAGE:
                value = self.table_operations.average(request.values)

            elif operation == ComputeOperation.MIN:
                value = self.table_operations.minimum(request.values)

            elif operation == ComputeOperation.MAX:
                value = self.table_operations.maximum(request.values)

            elif operation == ComputeOperation.COUNT:
                value = self.table_operations.count(request.values)

            else:
                return ComputeResult.failure(
                    operation=operation,
                    error=f"Unsupported compute operation: {operation}",
                )

            return ComputeResult.ok(
                operation=operation,
                value=value,
            )

        except TableOperationError as exc:
            return ComputeResult.failure(
                operation=request.operation,
                error=str(exc),
            )

        except Exception as exc:
            return ComputeResult.failure(
                operation=request.operation,
                error=f"{type(exc).__name__}: {exc}",
            )

    def sum(
        self,
        values: Iterable[Any],
    ) -> ComputeResult:
        """Calculate a local sum."""

        return self.execute(
            ComputeRequest(
                operation=ComputeOperation.SUM,
                values=list(values),
            )
        )

    def average(
        self,
        values: Iterable[Any],
    ) -> ComputeResult:
        """Calculate a local average."""

        return self.execute(
            ComputeRequest(
                operation=ComputeOperation.AVERAGE,
                values=list(values),
            )
        )

    def minimum(
        self,
        values: Iterable[Any],
    ) -> ComputeResult:
        """Calculate the local minimum."""

        return self.execute(
            ComputeRequest(
                operation=ComputeOperation.MIN,
                values=list(values),
            )
        )

    def maximum(
        self,
        values: Iterable[Any],
    ) -> ComputeResult:
        """Calculate the local maximum."""

        return self.execute(
            ComputeRequest(
                operation=ComputeOperation.MAX,
                values=list(values),
            )
        )

    def count(
        self,
        values: Iterable[Any],
    ) -> ComputeResult:
        """Count values locally."""

        return self.execute(
            ComputeRequest(
                operation=ComputeOperation.COUNT,
                values=list(values),
            )
        )
