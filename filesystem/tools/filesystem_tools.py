from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from ..filesystem_models import (
    FilesystemOperation,
    OperationType,
)
from ..filesystem_service import SandboxFilesystemService
from .tool_models import ToolResult


class FilesystemToolAdapter:
    """
    Adapter between generic tool calls and the sandboxed filesystem service.

    This class does NOT perform filesystem I/O itself.

    Every operation is converted into a FilesystemOperation and passed
    to SandboxFilesystemService, which remains the security boundary.
    """

    def __init__(self, service: SandboxFilesystemService) -> None:
        self.service = service

    def build_tools(self) -> list[tuple[str, str, dict, Any]]:
        """
        Return all filesystem tools in registry-ready form.
        """

        return [
            (
                "list_directory",
                "List the files and folders inside a sandbox-relative directory.",
                self._declaration_list_directory(),
                self.list_directory,
            ),
            (
                "search_files",
                (
                    "Search files inside a sandbox-relative directory. "
                    "Can filter by filename pattern and optionally "
                    "search file contents."
                ),
                self._declaration_search_files(),
                self.search_files,
            ),
            (
                "read_file",
                (
                    "Read the complete contents of a text file "
                    "using a sandbox-relative path."
                ),
                self._declaration_read_file(),
                self.read_file,
            ),
            (
                "read_table",
                "Read a CSV or JSON file as structured table data.",
                self._declaration_read_table(),
                self.read_table,
            ),
            (
                "calculate",
                "Evaluate a safe arithmetic expression.",
                self._declaration_calculate(),
                self.calculate,
            ),
            (
                "write_file",
                (
                    "Write or replace a text file. Use only when "
                    "the user explicitly asks to create or replace "
                    "file contents."
                ),
                self._declaration_write_file(),
                self.write_file,
            ),
            (
                "append_file",
                "Append text to an existing file.",
                self._declaration_append_file(),
                self.append_file,
            ),
            (
                "create_directory",
                "Create a directory inside the sandbox.",
                self._declaration_create_directory(),
                self.create_directory,
            ),
            (
                "delete_file",
                "Delete a file inside the sandbox.",
                self._declaration_delete_file(),
                self.delete_file,
            ),
            (
                "delete_directory",
                "Delete a directory inside the sandbox.",
                self._declaration_delete_directory(),
                self.delete_directory,
            ),
            (
                "move",
                "Move a file or directory within the sandbox.",
                self._declaration_move(),
                self.move,
            ),
            (
                "copy",
                "Copy a file or directory within the sandbox.",
                self._declaration_copy(),
                self.copy,
            ),
        ]





    def list_directory(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.LIST_DIRECTORY,
            arguments,
        )

        return self._execute(operation)

    def search_files(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.SEARCH_FILES,
            arguments,
        )

        return self._execute(operation)

    def read_file(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.READ_FILE,
            arguments,
        )

        return self._execute(operation)

    def read_table(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.READ_TABLE,
            arguments,
        )

        return self._execute(operation)

    def calculate(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.CALCULATE,
            arguments,
        )

        return self._execute(operation)

    def write_file(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.WRITE_FILE,
            arguments,
        )

        return self._execute(operation)

    def append_file(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.APPEND_FILE,
            arguments,
        )

        return self._execute(operation)

    def create_directory(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.CREATE_DIRECTORY,
            arguments,
        )

        return self._execute(operation)

    def delete_file(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.DELETE_FILE,
            arguments,
        )

        return self._execute(operation)

    def delete_directory(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.DELETE_DIRECTORY,
            arguments,
        )

        return self._execute(operation)

    def move(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.MOVE,
            arguments,
        )

        return self._execute(operation)

    def copy(self, arguments: dict[str, Any]) -> ToolResult:
        operation = self._operation(
            OperationType.COPY,
            arguments,
        )

        return self._execute(operation)





    @staticmethod
    def _operation(
        operation: OperationType,
        arguments: dict[str, Any],
    ) -> FilesystemOperation:
        """
        Convert generic tool arguments into the existing filesystem
        domain model.

        Validation and sandbox enforcement remain downstream in the
        filesystem service.
        """

        return FilesystemOperation(
            operation=operation,
            path=arguments.get("path"),
            destination=arguments.get("destination"),
            pattern=arguments.get("pattern"),
            query=arguments.get("query"),
            content=arguments.get("content"),
            expression=arguments.get("expression"),
            recursive=bool(arguments.get("recursive", False)),
            encoding=arguments.get("encoding", "utf-8"),
            options=arguments.get("options", {}),
        )

    def _execute(
        self,
        operation: FilesystemOperation,
    ) -> ToolResult:
        """
        Execute through SandboxFilesystemService.

        No filesystem Path operation is performed here.
        """

        result = self.service.execute(operation)

        if not result.success:
            return ToolResult.failure(
                name=operation.operation.value,
                error=result.message,
            )

        return ToolResult.ok(
            name=operation.operation.value,
            data=self._serialize(result.data),
            message=result.message,
        )





    @classmethod
    def _serialize(cls, value: Any) -> Any:
        if value is None:
            return None

        if is_dataclass(value):
            return cls._serialize(asdict(value))

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, list):
            return [cls._serialize(item) for item in value]

        if isinstance(value, tuple):
            return [cls._serialize(item) for item in value]

        if isinstance(value, dict):
            return {str(key): cls._serialize(item) for key, item in value.items()}

        if isinstance(value, (str, int, float, bool)):
            return value

        return str(value)





    @staticmethod
    def _declaration_list_directory() -> dict:
        return {
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
                    },
                },
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_search_files() -> dict:
        return {
            "name": "search_files",
            "description": ("Search files inside a sandbox-relative directory."),
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
                        "description": ("Optional text to search for inside files."),
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": ("Whether to search nested directories."),
                    },
                },
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_read_file() -> dict:
        return {
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
                        "description": "Sandbox-relative file path.",
                    },
                    "encoding": {
                        "type": "string",
                        "description": ("Text encoding. Normally use utf-8."),
                    },
                },
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_read_table() -> dict:
        return {
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
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_calculate() -> dict:
        return {
            "name": "calculate",
            "description": "Evaluate a safe arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": ("Arithmetic expression to evaluate."),
                    },
                },
                "required": ["expression"],
            },
        }

    @staticmethod
    def _declaration_write_file() -> dict:
        return {
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
        }

    @staticmethod
    def _declaration_append_file() -> dict:
        return {
            "name": "append_file",
            "description": "Append text to an existing file.",
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
        }

    @staticmethod
    def _declaration_create_directory() -> dict:
        return {
            "name": "create_directory",
            "description": ("Create a directory inside the sandbox."),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": ("Sandbox-relative directory path."),
                    },
                },
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_delete_file() -> dict:
        return {
            "name": "delete_file",
            "description": "Delete a file inside the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                },
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_delete_directory() -> dict:
        return {
            "name": "delete_directory",
            "description": ("Delete a directory inside the sandbox."),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                },
                "required": ["path"],
            },
        }

    @staticmethod
    def _declaration_move() -> dict:
        return {
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
        }

    @staticmethod
    def _declaration_copy() -> dict:
        return {
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
        }
