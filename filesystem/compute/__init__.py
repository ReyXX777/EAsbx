"""
Deterministic local compute subsystem.

This package provides CPU-local operations for structured data.
It contains no Gemini, Qt, filesystem, or UI dependencies.
"""

from .compute_models import (
    ComputeOperation,
    ComputeRequest,
    ComputeResult,
)
from .compute_service import ComputeService

__all__ = [
    "ComputeOperation",
    "ComputeRequest",
    "ComputeResult",
    "ComputeService",
]
