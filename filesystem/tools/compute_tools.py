from __future__ import annotations

from typing import Any

from ..compute.compute_models import ComputeOperation, ComputeRequest
from ..compute.compute_service import ComputeService
from .tool_models import ToolResult


class ComputeToolAdapter:
    """
    Adapter between generic tool calls and ComputeService.

    This adapter contains no Gemini or UI logic.
    """

    def __init__(self, service: ComputeService) -> None:
        self.service = service

    def build_tools(self) -> list[tuple[str, str, dict, Any]]:
        """
        Return all compute tools in registry-ready form.
        """

        return [
            (
                "compute_sum",
                "Calculate the sum of numeric table values.",
                self._declaration_sum(),
                self.sum,
            ),
            (
                "compute_average",
                "Calculate the arithmetic average of numeric table values.",
                self._declaration_average(),
                self.average,
            ),
            (
                "compute_min",
                "Find the minimum numeric value in table data.",
                self._declaration_min(),
                self.minimum,
            ),
            (
                "compute_max",
                "Find the maximum numeric value in table data.",
                self._declaration_max(),
                self.maximum,
            ),
            (
                "compute_count",
                "Count the supplied table values.",
                self._declaration_count(),
                self.count,
            ),
        ]

    # ==================================================================
    # Tool handlers
    # ==================================================================

    def sum(self, arguments: dict[str, Any]) -> ToolResult:
        return self._execute(
            tool_name="compute_sum",
            operation=ComputeOperation.SUM,
            arguments=arguments,
        )

    def average(self, arguments: dict[str, Any]) -> ToolResult:
        return self._execute(
            tool_name="compute_average",
            operation=ComputeOperation.AVERAGE,
            arguments=arguments,
        )

    def minimum(self, arguments: dict[str, Any]) -> ToolResult:
        return self._execute(
            tool_name="compute_min",
            operation=ComputeOperation.MIN,
            arguments=arguments,
        )

    def maximum(self, arguments: dict[str, Any]) -> ToolResult:
        return self._execute(
            tool_name="compute_max",
            operation=ComputeOperation.MAX,
            arguments=arguments,
        )

    def count(self, arguments: dict[str, Any]) -> ToolResult:
        return self._execute(
            tool_name="compute_count",
            operation=ComputeOperation.COUNT,
            arguments=arguments,
        )

    # ==================================================================
    # Compute boundary
    # ==================================================================

    def _execute(
        self,
        *,
        tool_name: str,
        operation: ComputeOperation,
        arguments: dict[str, Any],
    ) -> ToolResult:
        values = arguments.get("values")

        if not isinstance(values, list):
            return ToolResult.failure(
                name=tool_name,
                error="Tool argument 'values' must be a list.",
            )

        request = ComputeRequest(
            operation=operation,
            values=values,
        )

        result = self.service.execute(request)

        if not result.success:
            return ToolResult.failure(
                name=tool_name,
                error=result.error or "Compute operation failed.",
            )

        return ToolResult.ok(
            name=tool_name,
            data=result.value,
        )

    # ==================================================================
    # Tool declarations
    # ==================================================================

    @staticmethod
    def _values_schema() -> dict[str, Any]:
        return {
            "type": "array",
            "description": (
                "Values to process. Numeric values or numeric strings "
                "are accepted for arithmetic operations."
            ),
            "items": {},
        }

    @classmethod
    def _declaration_sum(cls) -> dict:
        return {
            "name": "compute_sum",
            "description": ("Calculate the sum of numeric table values."),
            "parameters": {
                "type": "object",
                "properties": {
                    "values": cls._values_schema(),
                },
                "required": ["values"],
            },
        }

    @classmethod
    def _declaration_average(cls) -> dict:
        return {
            "name": "compute_average",
            "description": (
                "Calculate the arithmetic average of numeric " "table values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "values": cls._values_schema(),
                },
                "required": ["values"],
            },
        }

    @classmethod
    def _declaration_min(cls) -> dict:
        return {
            "name": "compute_min",
            "description": ("Find the minimum numeric value in table data."),
            "parameters": {
                "type": "object",
                "properties": {
                    "values": cls._values_schema(),
                },
                "required": ["values"],
            },
        }

    @classmethod
    def _declaration_max(cls) -> dict:
        return {
            "name": "compute_max",
            "description": ("Find the maximum numeric value in table data."),
            "parameters": {
                "type": "object",
                "properties": {
                    "values": cls._values_schema(),
                },
                "required": ["values"],
            },
        }

    @classmethod
    def _declaration_count(cls) -> dict:
        return {
            "name": "compute_count",
            "description": ("Count the supplied table values."),
            "parameters": {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array",
                        "description": ("Values to count."),
                        "items": {},
                    },
                },
                "required": ["values"],
            },
        }
