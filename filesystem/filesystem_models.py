from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class OperationType(str, Enum):
    LIST_DIRECTORY = "list_directory"
    SEARCH_FILES = "search_files"
    READ_FILE = "read_file"
    READ_TABLE = "read_table"
    CALCULATE = "calculate"
    WRITE_FILE = "write_file"
    APPEND_FILE = "append_file"
    CREATE_DIRECTORY = "create_directory"
    DELETE_FILE = "delete_file"
    DELETE_DIRECTORY = "delete_directory"
    MOVE = "move"
    COPY = "copy"


@dataclass(frozen=True)
class FilesystemOperation:
    """Validated-domain description of one filesystem tool call."""

    operation: OperationType
    path: Optional[str] = None
    destination: Optional[str] = None
    pattern: Optional[str] = None
    query: Optional[str] = None
    content: Optional[str] = None
    expression: Optional[str] = None
    recursive: bool = False
    encoding: str = "utf-8"
    confirm_token: Optional[str] = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileEntry:
    name: str
    relative_path: str
    is_directory: bool
    size: int = 0
    modified_time: float = 0.0
    extension: str = ""


@dataclass
class FilesystemResult:
    operation: OperationType
    success: bool
    data: Any = None
    message: str = ""
    relative_path: Optional[str] = None

    @classmethod
    def ok(
        cls,
        operation: OperationType,
        data: Any = None,
        message: str = "",
        relative_path: Optional[str] = None,
    ) -> "FilesystemResult":
        return cls(
            operation=operation,
            success=True,
            data=data,
            message=message,
            relative_path=relative_path,
        )

    @classmethod
    def error(
        cls,
        operation: OperationType,
        message: str,
    ) -> "FilesystemResult":
        return cls(operation=operation, success=False, message=message)
