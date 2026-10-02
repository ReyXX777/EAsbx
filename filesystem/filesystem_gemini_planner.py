from __future__ import annotations

from typing import Any, Callable

from google import genai
from google.genai import types

from .tools.tool_dispatcher import ToolDispatcher
from .tools.tool_models import ToolCall, ToolResult


class GeminiFilesystemPlannerError(RuntimeError):
    """Raised when Gemini cannot produce or execute a filesystem plan."""


class GeminiFilesystemToolPlanner:
    """
    Gemini-powered tool planner for the MOCKAPP agent suite.

    Gemini does not perform filesystem or compute operations directly.

    Instead:

        Gemini
            ↓
        ToolCall
            ↓
        ToolDispatcher
            ↓
        ToolRegistry
            ↓
        FilesystemToolAdapter / ComputeToolAdapter
            ↓
        SandboxFilesystemService / ComputeService

    Gemini only receives the tool declarations exposed by the
    ToolDispatcher. Physical filesystem paths are never exposed to Gemini.
    """

    MODEL = "gemini-3.5-flash-lite"

    MAX_TOOL_ROUNDS = 20

    def __init__(
        self,
        api_key: str,
        tool_dispatcher: ToolDispatcher,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required.")

        if not isinstance(tool_dispatcher, ToolDispatcher):
            raise TypeError("tool_dispatcher must be a ToolDispatcher instance.")

        self.api_key = api_key
        self.tool_dispatcher = tool_dispatcher

        self.client = genai.Client(
            api_key=api_key,
        )

    # ==================================================================
    # Public execution interface
    # ==================================================================

    def execute(
        self,
        prompt: str,
        *,
        on_tool_call: Callable[[ToolCall], None] | None = None,
        on_result: Callable[[ToolCall, ToolResult], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> tuple[list[ToolResult], str]:
        """
        Execute a Gemini-driven tool loop.

        Gemini may request multiple tools across multiple rounds.

        Each function call is converted into a generic ToolCall and sent
        through ToolDispatcher. The resulting ToolResult is then returned
        to Gemini.
        """

        contents: list[Any] = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=prompt,
                    )
                ],
            )
        ]

        results: list[ToolResult] = []

        config = self._build_config()

        for _round in range(self.MAX_TOOL_ROUNDS):

            if should_cancel is not None and should_cancel():
                raise GeminiFilesystemPlannerError("Filesystem task was cancelled.")

            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=contents,
                config=config,
            )

            if not response.candidates:
                raise GeminiFilesystemPlannerError("Gemini returned no candidates.")

            model_content = response.candidates[0].content

            if model_content is None:
                raise GeminiFilesystemPlannerError(
                    "Gemini returned an empty response content."
                )

            function_calls = []

            for part in model_content.parts or []:

                function_call = getattr(
                    part,
                    "function_call",
                    None,
                )

                if function_call is not None:
                    function_calls.append(function_call)

            # ----------------------------------------------------------
            # No function call means Gemini has produced its final answer.
            # ----------------------------------------------------------

            if not function_calls:

                final_text = (
                    response.text
                    or "Filesystem task completed without a final response."
                )

                return results, final_text

            # ----------------------------------------------------------
            # Preserve the complete Gemini model response.
            #
            # This is important for Gemini 3 function-call/thinking
            # context preservation.
            # ----------------------------------------------------------

            contents.append(model_content)

            function_response_parts = []

            for function_call in function_calls:

                tool_call = self._tool_call_from_function_call(function_call)

                if on_tool_call is not None:
                    on_tool_call(tool_call)
                if should_cancel is not None and should_cancel():
                    raise GeminiFilesystemPlannerError("Filesystem task was cancelled.")

                result = self.tool_dispatcher.dispatch(tool_call)

                results.append(result)

                if on_result is not None:
                    on_result(
                        tool_call,
                        result,
                    )

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={
                            "result": result.to_dict(),
                        },
                    )
                )

            contents.append(
                types.Content(
                    role="user",
                    parts=function_response_parts,
                )
            )

        raise GeminiFilesystemPlannerError(
            f"Filesystem agent exceeded the maximum "
            f"tool-call rounds ({self.MAX_TOOL_ROUNDS})."
        )

    # ==================================================================
    # Gemini configuration
    # ==================================================================

    def _build_config(self) -> types.GenerateContentConfig:
        """
        Build the Gemini configuration from the registered tools.

        The planner does not define filesystem or compute tools itself.
        """

        system_instruction = """
You are the filesystem and computation agent for MOCKAPP.

You operate ONLY through the tools supplied to you.

IMPORTANT SANDBOX RULES:

1. You never receive or need the physical Windows filesystem root.
2. Every filesystem path must be sandbox-relative.
3. Never use:
   - C:\\
   - X:\\
   - UNC paths
   - absolute paths
   - parent traversal such as ../ or ..\\
4. Do not invent file contents.
5. Use filesystem tools to inspect the filesystem before answering.
6. When the user asks you to navigate, use list_directory to inspect
   the requested directory and continue from the returned entries.
7. When the user asks you to read a file, use read_file.
8. When the user asks you to search for content, use search_files.
9. Use read_table when structured CSV or JSON table data is required.
10. Use compute tools when numerical calculations over supplied values
    are required.
11. Prefer the smallest number of tool operations necessary.
12. Do not perform write, delete, move, copy, or directory-creation
    operations unless the user explicitly requested that operation.
13. Do not access files through any mechanism other than the supplied
    filesystem tools.
14. After obtaining the required information, provide a concise final
    answer containing the requested information and relevant relative
    file paths.

The supplied tools are the ONLY mechanism you may use to access files
or perform computations.
"""

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[
                types.Tool(function_declarations=self.tool_dispatcher.declarations())
            ],
            thinking_config=types.ThinkingConfig(thinking_level="medium"),
        )

    # ==================================================================
    # Gemini function call → generic ToolCall
    # ==================================================================

    @staticmethod
    def _tool_call_from_function_call(
        function_call: Any,
    ) -> ToolCall:
        """
        Convert a Gemini function call into the provider-neutral
        ToolCall model.

        No filesystem-specific conversion happens here.
        """

        name = getattr(
            function_call,
            "name",
            None,
        )

        if not name:
            raise GeminiFilesystemPlannerError(
                "Gemini returned a function call without a tool name."
            )

        arguments = dict(
            getattr(
                function_call,
                "args",
                None,
            )
            or {}
        )

        return ToolCall(
            name=name,
            arguments=arguments,
        )
