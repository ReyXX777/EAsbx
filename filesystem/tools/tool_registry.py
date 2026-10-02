from __future__ import annotations

from collections.abc import Iterable

from .tool_models import ToolHandler, ToolSpec


class ToolRegistryError(RuntimeError):
    """Raised when a tool registry operation is invalid."""


class ToolRegistry:
    """
    Central registry of available tools.

    The registry knows which tools exist, but it does not know
    how Gemini or another model calls them.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(
        self,
        *,
        name: str,
        description: str,
        declaration: dict,
        handler: ToolHandler,
    ) -> ToolSpec:
        """
        Register one tool.
        """

        if not name or not name.strip():
            raise ToolRegistryError("Tool name must be a non-empty string.")

        if name in self._tools:
            raise ToolRegistryError(f"Tool is already registered: {name}")

        spec = ToolSpec(
            name=name,
            description=description,
            declaration=declaration,
            handler=handler,
        )

        self._tools[name] = spec
        return spec

    def register_spec(self, spec: ToolSpec) -> ToolSpec:
        """
        Register an already-created ToolSpec.
        """

        if spec.name in self._tools:
            raise ToolRegistryError(f"Tool is already registered: {spec.name}")

        self._tools[spec.name] = spec
        return spec

    def register_many(self, specs: Iterable[ToolSpec]) -> None:
        """
        Register multiple tools.
        """

        for spec in specs:
            self.register_spec(spec)

    def get(self, name: str) -> ToolSpec:
        """
        Return a registered tool.
        """

        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolRegistryError(f"Unknown tool: {name}") from exc

    def contains(self, name: str) -> bool:
        """
        Return whether a tool is registered.
        """

        return name in self._tools

    def names(self) -> list[str]:
        """
        Return registered tool names in registration order.
        """

        return list(self._tools.keys())

    def specs(self) -> list[ToolSpec]:
        """
        Return all registered tool specifications.
        """

        return list(self._tools.values())

    def declarations(self) -> list[dict]:
        """
        Return declarations for all registered tools.

        The declarations remain plain dictionaries so this class
        remains independent of Gemini's SDK.
        """

        return [spec.as_declaration() for spec in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return self.contains(name)
