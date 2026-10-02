from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

ToolHandler = Callable[[dict[str, Any]], "ToolResult"]


@dataclass(frozen=True)
class ToolCall:
    """
    Generic representation of one tool invocation.

    This model intentionally knows nothing about Gemini,
    filesystem operations, compute operations, or UI code.
    """

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """
    Generic result returned by a tool.

    The dispatcher uses this as the common boundary between
    individual tool implementations and the caller.
    """

    name: str
    success: bool
    data: Any = None
    message: str = ""
    error: str | None = None

    @classmethod
    def ok(
        cls,
        name: str,
        data: Any = None,
        message: str = "",
    ) -> "ToolResult":
        return cls(
            name=name,
            success=True,
            data=data,
            message=message,
            error=None,
        )

    @classmethod
    def failure(
        cls,
        name: str,
        error: str,
    ) -> "ToolResult":
        return cls(
            name=name,
            success=False,
            data=None,
            message="",
            error=error,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a stable dictionary representation suitable for
        serialization and passing back to an external caller.
        """

        return {
            "tool": self.name,
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
        }


@dataclass(frozen=True)
class ToolSpec:
    """
    Description of one registered tool.

    `declaration` is intentionally represented as a plain dictionary
    so the registry remains independent of any particular AI SDK.
    """

    name: str
    description: str
    declaration: dict[str, Any]
    handler: ToolHandler

    def as_declaration(self) -> dict[str, Any]:
        """
        Return the external tool declaration.

        The declaration can later be converted into the format
        expected by Gemini, another model provider, or another
        tool-calling system.
        """

        return self.declaration
