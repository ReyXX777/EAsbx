from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from google import genai
from google.genai import types

from .filesystem_models import (
    FilesystemOperation,
    FilesystemResult,
    OperationType,
)


class GeminiFilesystemPlannerError(RuntimeError):
    """Raised when Gemini cannot produce or execute a filesystem plan."""


class GeminiFilesystemToolPlanner:
    """
    Gemini-powered filesystem tool planner.

    Gemini never receives the physical sandbox root.

    It only sees sandbox-relative filesystem paths and the declared
    filesystem tools.

    Tool execution is delegated back to the caller through
    `execute_operation`, which ultimately reaches SandboxFilesystemService.
    """

    MODEL = "gemini-3.5-flash-lite"

    MAX_TOOL_ROUNDS = 20

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required.")

        self.api_key = api_key

        self.client = genai.Client(
            api_key=api_key,
        )

    # ==============================================================
    # Public execution interface
    # ==============================================================

    def execute(
        self,
        prompt: str,
        execute_operation: Callable[
            [FilesystemOperation],
            FilesystemResult,
        ],
        *,
        on_result: (
            Callable[[FilesystemOperation, FilesystemResult], None] | None
        ) = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> tuple[list[FilesystemResult], str]:

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

        results: list[FilesystemResult] = []

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
            # No function call = Gemini has produced its final answer.
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

                operation = self._operation_from_function_call(function_call)

                if should_cancel is not None and should_cancel():
                    raise GeminiFilesystemPlannerError("Filesystem task was cancelled.")

                result = execute_operation(operation)

                results.append(result)

                if on_result is not None:
                    on_result(
                        operation,
                        result,
                    )

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={
                            "result": self._serialize_result(result),
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

    # ==============================================================
    # Gemini configuration
    # ==============================================================

    def _build_config(self) -> types.GenerateContentConfig:

        system_instruction = """
You are the filesystem agent for MOCKAPP.

You operate ONLY through the filesystem tools supplied to you.

IMPORTANT SANDBOX RULES:

1. You never receive or need the physical Windows filesystem root.
2. Every path must be sandbox-relative.
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
9. Prefer the smallest number of filesystem operations necessary.
10. Do not perform write, delete, move, copy, or directory-creation
    operations unless the user explicitly requested that operation.
11. After obtaining the required information, provide a concise final
    answer containing the requested information and relevant relative
    file paths.

The filesystem tools are the ONLY mechanism you may use to access files.
"""

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(function_declarations=self._tool_declarations())],
            thinking_config=types.ThinkingConfig(thinking_level="medium"),
        )

    # ==============================================================
    # Gemini tool declarations
    # ==============================================================

    @staticmethod
    def _tool_declarations() -> list[dict[str, Any]]:

        return [
            # ----------------------------------------------------------
            # LIST DIRECTORY
            # ----------------------------------------------------------
            {
                "name": "list_directory",
                "description": (
                    "List the files and folders inside a " "sandbox-relative directory."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "Sandbox-relative directory path. "
                                "Use '.' for the filesystem root."
                            ),
                        }
                    },
                    "required": ["path"],
                },
            },
            # ----------------------------------------------------------
            # SEARCH FILES
            # ----------------------------------------------------------
            {
                "name": "search_files",
                "description": (
                    "Search files inside a sandbox-relative directory. "
                    "Can filter by filename pattern and optionally "
                    "search file contents."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": ("Sandbox-relative directory to search."),
                        },
                        "pattern": {
                            "type": "string",
                            "description": ("Filename pattern such as '*.txt'."),
                        },
                        "query": {
                            "type": "string",
                            "description": (
                                "Optional text to search for inside files."
                            ),
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": ("Whether to search nested directories."),
                        },
                    },
                    "required": [
                        "path",
                    ],
                },
            },
            # ----------------------------------------------------------
            # READ FILE
            # ----------------------------------------------------------
            {
                "name": "read_file",
                "description": (
                    "Read the complete contents of a text file "
                    "using a sandbox-relative path."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": ("Sandbox-relative file path."),
                        },
                        "encoding": {
                            "type": "string",
                            "description": ("Text encoding. Normally use utf-8."),
                        },
                    },
                    "required": [
                        "path",
                    ],
                },
            },
            # ----------------------------------------------------------
            # READ TABLE
            # ----------------------------------------------------------
            {
                "name": "read_table",
                "description": ("Read a CSV or JSON file as structured table data."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": ("Sandbox-relative CSV or JSON file path."),
                        },
                        "encoding": {
                            "type": "string",
                            "description": ("Text encoding. Normally use utf-8."),
                        },
                    },
                    "required": [
                        "path",
                    ],
                },
            },
            # ----------------------------------------------------------
            # CALCULATE
            # ----------------------------------------------------------
            {
                "name": "calculate",
                "description": ("Evaluate a safe arithmetic expression."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": ("Arithmetic expression to evaluate."),
                        }
                    },
                    "required": ["expression"],
                },
            },
            # ----------------------------------------------------------
            # WRITE FILE
            # ----------------------------------------------------------
            {
                "name": "write_file",
                "description": (
                    "Write or replace a text file. Use only when "
                    "the user explicitly asks to create or replace "
                    "file contents."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Sandbox-relative file path.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Complete file contents.",
                        },
                        "encoding": {
                            "type": "string",
                            "description": "Text encoding.",
                        },
                    },
                    "required": [
                        "path",
                        "content",
                        "encoding",
                    ],
                },
            },
            # ----------------------------------------------------------
            # APPEND FILE
            # ----------------------------------------------------------
            {
                "name": "append_file",
                "description": ("Append text to an existing file."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        },
                        "content": {
                            "type": "string",
                        },
                        "encoding": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "path",
                        "content",
                        "encoding",
                    ],
                },
            },
            # ----------------------------------------------------------
            # CREATE DIRECTORY
            # ----------------------------------------------------------
            {
                "name": "create_directory",
                "description": ("Create a directory inside the sandbox."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": ("Sandbox-relative directory path."),
                        }
                    },
                    "required": ["path"],
                },
            },
            # ----------------------------------------------------------
            # DELETE FILE
            # ----------------------------------------------------------
            {
                "name": "delete_file",
                "description": ("Delete a file inside the sandbox."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        }
                    },
                    "required": ["path"],
                },
            },
            # ----------------------------------------------------------
            # DELETE DIRECTORY
            # ----------------------------------------------------------
            {
                "name": "delete_directory",
                "description": ("Delete a directory inside the sandbox."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        }
                    },
                    "required": ["path"],
                },
            },
            # ----------------------------------------------------------
            # MOVE
            # ----------------------------------------------------------
            {
                "name": "move",
                "description": ("Move a file or directory within the sandbox."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        },
                        "destination": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "path",
                        "destination",
                    ],
                },
            },
            # ----------------------------------------------------------
            # COPY
            # ----------------------------------------------------------
            {
                "name": "copy",
                "description": ("Copy a file or directory within the sandbox."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                        },
                        "destination": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "path",
                        "destination",
                    ],
                },
            },
        ]

    # ==============================================================
    # Function-call → domain operation
    # ==============================================================

    @staticmethod
    def _operation_from_function_call(
        function_call: Any,
    ) -> FilesystemOperation:

        name = function_call.name
        args = dict(function_call.args or {})

        try:
            operation_type = OperationType(name)
        except ValueError as exc:
            raise GeminiFilesystemPlannerError(
                f"Gemini requested unsupported filesystem tool: {name}"
            ) from exc

        # Never accept physical filesystem paths from Gemini.
        path = args.get("path")

        destination = args.get("destination")

        pattern = args.get("pattern")

        query = args.get("query")

        content = args.get("content")

        expression = args.get("expression")

        recursive = bool(
            args.get(
                "recursive",
                False,
            )
        )

        encoding = args.get(
            "encoding",
            "utf-8",
        )

        return FilesystemOperation(
            operation=operation_type,
            path=path,
            destination=destination,
            pattern=pattern,
            query=query,
            content=content,
            expression=expression,
            recursive=recursive,
            encoding=encoding,
        )

    # ==============================================================
    # Result serialization
    # ==============================================================

    @classmethod
    def _serialize_result(
        cls,
        result: FilesystemResult,
    ) -> dict[str, Any]:

        return {
            "operation": result.operation.value,
            "success": result.success,
            "message": result.message,
            "relative_path": result.relative_path,
            "data": cls._serialize_value(result.data),
        }

    @classmethod
    def _serialize_value(
        cls,
        value: Any,
    ) -> Any:

        if value is None:
            return None

        if is_dataclass(value):
            return cls._serialize_value(asdict(value))

        if isinstance(value, list):
            return [cls._serialize_value(item) for item in value]

        if isinstance(value, tuple):
            return [cls._serialize_value(item) for item in value]

        if isinstance(value, dict):
            return {str(key): cls._serialize_value(item) for key, item in value.items()}

        if hasattr(value, "value"):
            return value.value

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        return str(value)
