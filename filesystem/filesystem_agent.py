from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .filesystem_service import SandboxFilesystemService
from .tools.tool_dispatcher import ToolDispatcher
from .tools.tool_models import ToolCall, ToolResult


class FilesystemAgentError(RuntimeError):
    """Raised when the filesystem agent cannot execute a task."""


@dataclass
class FilesystemAgent:
    """
    Tool-mediated filesystem agent.

    The agent is an orchestration layer between the worker and the
    Gemini planner.

    Tool execution is delegated to ToolDispatcher.

    The agent itself does not:

        - perform filesystem I/O
        - perform computation
        - register tools
        - implement tool handlers
        - know individual filesystem/compute tool implementations

    Architecture:

        FilesystemAgent
              ↓
        GeminiFilesystemToolPlanner
              ↓
        ToolDispatcher
          ├── FilesystemToolAdapter
          │       ↓
          │   SandboxFilesystemService
          │
          └── ComputeToolAdapter
                  ↓
              ComputeService
    """

    service: SandboxFilesystemService
    planner: Any
    tool_dispatcher: ToolDispatcher





    def execute_tool(
        self,
        call: ToolCall,
    ) -> ToolResult:
        """
        Execute one generic tool call through ToolDispatcher.

        The agent does not know whether the tool is a filesystem
        tool, compute tool, or another future tool type.
        """

        return self.tool_dispatcher.dispatch(call)





    def run_interactive(
        self,
        prompt: str,
        *,
        on_tool_call: Callable[[ToolCall], None] | None = None,
        on_result: Callable[[ToolCall, ToolResult], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> tuple[list[ToolResult], str]:
        """
        Run the interactive planner/tool loop.

        The planner already owns the ToolDispatcher used by the
        Gemini tool-calling loop.

        The agent therefore delegates execution to the planner
        without passing a second dispatcher instance.

        This keeps the tool execution path:

            Gemini
                ↓
            ToolDispatcher
                ↓
            ToolRegistry
                ↓
            ToolAdapter
                ↓
            Domain Service
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
            on_tool_call=on_tool_call,
            on_result=on_result,
            should_cancel=should_cancel,
        )





    def execute_tool_call(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        """
        Convenience method for executing a tool by name.
        """

        return self.tool_dispatcher.dispatch_name(
            name=name,
            arguments=arguments or {},
        )





    def available_tools(self) -> list[str]:
        """
        Return the currently registered tool names.
        """

        return self.tool_dispatcher.available_tools()

    def tool_declarations(self) -> list[dict[str, Any]]:
        """
        Return provider-neutral tool declarations.

        Gemini-specific conversion remains the responsibility of
        GeminiFilesystemToolPlanner.
        """

        return self.tool_dispatcher.declarations()
