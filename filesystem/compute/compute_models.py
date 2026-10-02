from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ComputeOperation(str, Enum):
    """
    Supported deterministic compute operations.

    These operations are intentionally independent from any
    filesystem or UI implementation.
    """

    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


@dataclass(frozen=True)
class ComputeRequest:
    """
    Describes one deterministic computation.

    The compute layer receives structured data from another
    subsystem and performs the requested operation locally.
    """

    operation: ComputeOperation
    values: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class ComputeResult:
    """
    Result returned by the local compute subsystem.
    """

    operation: ComputeOperation
    value: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None

    @classmethod
    def ok(
        cls,
        operation: ComputeOperation,
        value: Any,
    ) -> "ComputeResult":
        return cls(
            operation=operation,
            value=value,
            success=True,
            error=None,
        )

    @classmethod
    def failure(
        cls,
        operation: ComputeOperation,
        error: str,
    ) -> "ComputeResult":
        return cls(
            operation=operation,
            value=None,
            success=False,
            error=error,
        )
