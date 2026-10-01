from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol

from .filesystem_models import FilesystemOperation, FilesystemResult
from .filesystem_service import SandboxFilesystemService


class FilesystemAgentError(RuntimeError):
    pass


class FilesystemPlanner(Protocol):
    def plan(self, prompt: str) -> Iterable[FilesystemOperation]: ...


@dataclass
class FilesystemAgent:
    """
    Tool-mediated filesystem agent.

    The agent does not receive a raw machine path and does not perform direct
    filesystem I/O. It only submits structured operations to the service.
    """

    service: SandboxFilesystemService
    planner: (
        FilesystemPlanner | Callable[[str], Iterable[FilesystemOperation]] | None
    ) = None

    def execute_operation(self, operation: FilesystemOperation) -> FilesystemResult:
        return self.service.execute(operation)

    def execute_operations(
        self,
        operations: Iterable[FilesystemOperation],
        *,
        stop_on_error: bool = True,
        on_result: Callable[[FilesystemResult], None] | None = None,
    ) -> list[FilesystemResult]:
        results: list[FilesystemResult] = []

        for operation in operations:
            result = self.execute_operation(operation)
            results.append(result)

            if on_result is not None:
                on_result(result)

            if stop_on_error and not result.success:
                break

        return results

    def run(self, prompt: str, *, on_result=None) -> list[FilesystemResult]:
        if self.planner is None:
            raise FilesystemAgentError(
                "No filesystem planner is configured. "
                "Gemini/tool planning must produce FilesystemOperation objects."
            )

        if hasattr(self.planner, "plan"):
            operations = self.planner.plan(prompt)
        else:
            operations = self.planner(prompt)

        return self.execute_operations(
            operations,
            on_result=on_result,
        )

    def run_interactive(
        self,
        prompt: str,
        *,
        on_result=None,
        should_cancel=None,
    ) -> tuple[list[FilesystemResult], str]:
        """
        Run an interactive planner/tool loop.

        The planner receives the agent's execute_operation callback.
        This allows Gemini to:

            1. request a filesystem operation
            2. receive its result
            3. reason about that result
            4. request the next operation
            5. continue until the task is complete

        The actual filesystem operation still goes through
        SandboxFilesystemService.
        """

        if self.planner is None:
            raise FilesystemAgentError("No filesystem planner is configured.")

        interactive_execute = getattr(
            self.planner,
            "execute",
            None,
        )

        if not callable(interactive_execute):
            raise FilesystemAgentError(
                "Configured filesystem planner does not support "
                "interactive tool execution."
            )

        return interactive_execute(
            prompt,
            self.execute_operation,
            on_result=on_result,
            should_cancel=should_cancel,
        )

    @staticmethod
    def operation_to_tool_call(operation: FilesystemOperation) -> dict[str, Any]:
        """Stable serialization boundary for a future Gemini tool adapter."""
        return {
            "name": operation.operation.value,
            "arguments": {
                key: value
                for key, value in {
                    "path": operation.path,
                    "destination": operation.destination,
                    "pattern": operation.pattern,
                    "query": operation.query,
                    "content": operation.content,
                    "expression": operation.expression,
                    "recursive": operation.recursive,
                    "encoding": operation.encoding,
                    "options": operation.options,
                }.items()
                if value is not None
            },
        }
