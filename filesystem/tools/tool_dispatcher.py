from __future__ import annotations

from typing import Any

from .tool_models import ToolCall, ToolResult
from .tool_registry import ToolRegistry, ToolRegistryError


class ToolDispatcherError(RuntimeError):
    """Raised when a tool cannot be dispatched."""


class ToolDispatcher:
    """
    Central execution boundary for all registered tools.

    The dispatcher does not implement filesystem or compute logic.

    Its only responsibility is:

        ToolCall
            ↓
        ToolRegistry
            ↓
        registered handler
            ↓
        ToolResult
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def dispatch(self, call: ToolCall) -> ToolResult:
        """
        Execute one generic tool call.
        """

        if not isinstance(call, ToolCall):
            raise TypeError("dispatch() requires a ToolCall.")

        try:
            spec = self.registry.get(call.name)
        except ToolRegistryError as exc:
            return ToolResult.failure(
                name=call.name,
                error=str(exc),
            )

        try:
            arguments = dict(call.arguments or {})

            result = spec.handler(arguments)

            if not isinstance(result, ToolResult):
                return ToolResult.failure(
                    name=call.name,
                    error=(
                        f"Tool handler returned an invalid result type: "
                        f"{type(result).__name__}"
                    ),
                )

            return result

        except Exception as exc:
            return ToolResult.failure(
                name=call.name,
                error=f"{type(exc).__name__}: {exc}",
            )

    def dispatch_name(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        """
        Convenience wrapper for callers that already have a tool name
        and argument dictionary.
        """

        return self.dispatch(
            ToolCall(
                name=name,
                arguments=arguments or {},
            )
        )

    def declarations(self) -> list[dict]:
        """
        Return all registered tool declarations.

        The caller can adapt these declarations to Gemini or another
        model provider.
        """

        return self.registry.declarations()

    def available_tools(self) -> list[str]:
        """
        Return the names of all currently available tools.
        """

        return self.registry.names()
