from __future__ import annotations

from pathlib import Path

from .filesystem_models import FilesystemOperation, FilesystemResult, OperationType
from .filesystem_operations import FilesystemOperations
from .filesystem_sandbox import SandboxValidator


class SandboxFilesystemService:
    """
    Public service boundary.

    No caller should touch Path/file APIs directly. Every filesystem operation
    goes through this service, which delegates to sandboxed operations.
    """

    def __init__(self, sandbox_root: str | Path) -> None:
        self.sandbox = SandboxValidator(sandbox_root)
        self.operations = FilesystemOperations(self.sandbox)

    @property
    def root(self) -> Path:
        return self.sandbox.root

    def execute(self, operation: FilesystemOperation) -> FilesystemResult:
        return self.operations.dispatch(operation)

    def list_directory(self, path: str = ".", **kwargs):
        return self.execute(
            FilesystemOperation(OperationType.LIST_DIRECTORY, path=path, **kwargs)
        )

    def search_files(self, path: str = ".", pattern: str = "*", query: str = "",
                     recursive: bool = True, **kwargs):
        return self.execute(
            FilesystemOperation(
                OperationType.SEARCH_FILES,
                path=path,
                pattern=pattern,
                query=query,
                recursive=recursive,
                **kwargs,
            )
        )

    def read_file(self, path: str, **kwargs):
        return self.execute(
            FilesystemOperation(OperationType.READ_FILE, path=path, **kwargs)
        )

    def read_table(self, path: str, **kwargs):
        return self.execute(
            FilesystemOperation(OperationType.READ_TABLE, path=path, **kwargs)
        )

    def calculate(self, expression: str):
        return self.execute(
            FilesystemOperation(OperationType.CALCULATE, expression=expression)
        )

    def write_file(self, path: str, content: str, **kwargs):
        return self.execute(
            FilesystemOperation(
                OperationType.WRITE_FILE, path=path, content=content, **kwargs
            )
        )

    def append_file(self, path: str, content: str, **kwargs):
        return self.execute(
            FilesystemOperation(
                OperationType.APPEND_FILE, path=path, content=content, **kwargs
            )
        )

    def create_directory(self, path: str):
        return self.execute(
            FilesystemOperation(OperationType.CREATE_DIRECTORY, path=path)
        )

    def delete_file(self, path: str):
        return self.execute(
            FilesystemOperation(OperationType.DELETE_FILE, path=path)
        )

    def delete_directory(self, path: str):
        return self.execute(
            FilesystemOperation(OperationType.DELETE_DIRECTORY, path=path)
        )

    def move(self, path: str, destination: str):
        return self.execute(
            FilesystemOperation(
                OperationType.MOVE, path=path, destination=destination
            )
        )

    def copy(self, path: str, destination: str):
        return self.execute(
            FilesystemOperation(
                OperationType.COPY, path=path, destination=destination
            )
        )
