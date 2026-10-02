from __future__ import annotations

import ast
import csv
import fnmatch
import json
import math
import operator
import shutil
from pathlib import Path
from typing import Any, Iterable

from .filesystem_models import (
    FileEntry,
    FilesystemOperation,
    FilesystemResult,
    OperationType,
)
from .filesystem_sandbox import SandboxValidator
from .filesystem_validator import FilesystemInputValidator


class OperationError(RuntimeError):
    pass


class FilesystemOperations:
    """Low-level, sandboxed filesystem tools."""

    def __init__(self, sandbox: SandboxValidator) -> None:
        self.sandbox = sandbox

    def dispatch(self, operation: FilesystemOperation) -> FilesystemResult:
        handlers = {
            OperationType.LIST_DIRECTORY: self.list_directory,
            OperationType.SEARCH_FILES: self.search_files,
            OperationType.READ_FILE: self.read_file,
            OperationType.READ_TABLE: self.read_table,
            OperationType.CALCULATE: self.calculate,
            OperationType.WRITE_FILE: self.write_file,
            OperationType.APPEND_FILE: self.append_file,
            OperationType.CREATE_DIRECTORY: self.create_directory,
            OperationType.DELETE_FILE: self.delete_file,
            OperationType.DELETE_DIRECTORY: self.delete_directory,
            OperationType.MOVE: self.move,
            OperationType.COPY: self.copy,
        }
        handler = handlers.get(operation.operation)
        if handler is None:
            return FilesystemResult.error(
                operation.operation, f"Unsupported operation: {operation.operation}"
            )
        try:
            return handler(operation)
        except Exception as exc:
            return FilesystemResult.error(
                operation.operation, f"{type(exc).__name__}: {exc}"
            )

    def list_directory(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.resolve(op.path or ".", must_be_directory=True)
        entries: list[FileEntry] = []

        for item in sorted(
            path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        ):
            stat = item.stat()
            entries.append(
                FileEntry(
                    name=item.name,
                    relative_path=self.sandbox.relative_to_root(item),
                    is_directory=item.is_dir(),
                    size=0 if item.is_dir() else stat.st_size,
                    modified_time=stat.st_mtime,
                    extension="" if item.is_dir() else item.suffix.lower(),
                )
            )

        return FilesystemResult.ok(
            op.operation,
            data=entries,
            relative_path=self.sandbox.relative_to_root(path),
        )

    def search_files(self, op: FilesystemOperation) -> FilesystemResult:
        root = self.sandbox.resolve(op.path or ".", must_be_directory=True)
        pattern = FilesystemInputValidator.pattern(op.pattern)
        query = FilesystemInputValidator.text_query(op.query)
        results: list[FileEntry] = []

        iterator: Iterable[Path] = root.rglob("*") if op.recursive else root.glob("*")
        for item in iterator:
            if not item.is_file() or not fnmatch.fnmatch(item.name, pattern):
                continue

            if query:
                try:
                    text = item.read_text(
                        encoding=FilesystemInputValidator.encoding(op.encoding),
                        errors="ignore",
                    )
                except (UnicodeError, OSError):
                    continue
                if query.casefold() not in text.casefold():
                    continue

            stat = item.stat()
            results.append(
                FileEntry(
                    name=item.name,
                    relative_path=self.sandbox.relative_to_root(item),
                    is_directory=False,
                    size=stat.st_size,
                    modified_time=stat.st_mtime,
                    extension=item.suffix.lower(),
                )
            )

        results.sort(key=lambda x: x.relative_path.lower())
        return FilesystemResult.ok(op.operation, data=results)

    def read_file(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.resolve(op.path or "", must_be_directory=False)
        encoding = FilesystemInputValidator.encoding(op.encoding)
        content = path.read_text(encoding=encoding)
        return FilesystemResult.ok(
            op.operation,
            data=content,
            relative_path=self.sandbox.relative_to_root(path),
        )

    def read_table(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.resolve(op.path or "", must_be_directory=False)
        encoding = FilesystemInputValidator.encoding(op.encoding)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            with path.open("r", encoding=encoding, newline="") as handle:
                data = list(csv.DictReader(handle))
        elif suffix == ".json":
            with path.open("r", encoding=encoding) as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                raise OperationError("JSON table data must be an object or array.")
        else:
            raise OperationError("read_table currently supports .csv and .json files.")

        return FilesystemResult.ok(
            op.operation,
            data=data,
            relative_path=self.sandbox.relative_to_root(path),
        )

    def calculate(self, op: FilesystemOperation) -> FilesystemResult:
        expression = FilesystemInputValidator.expression(op.expression or "")
        value = _SafeCalculator().evaluate(expression)
        return FilesystemResult.ok(op.operation, data=value)

    def write_file(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.ensure_destination_parent(op.path or "")
        encoding = FilesystemInputValidator.encoding(op.encoding)
        path.write_text(op.content or "", encoding=encoding)
        return FilesystemResult.ok(
            op.operation,
            message="File written.",
            relative_path=self.sandbox.relative_to_root(path),
        )

    def append_file(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.ensure_destination_parent(op.path or "")
        encoding = FilesystemInputValidator.encoding(op.encoding)
        with path.open("a", encoding=encoding) as handle:
            handle.write(op.content or "")
        return FilesystemResult.ok(
            op.operation,
            message="File updated.",
            relative_path=self.sandbox.relative_to_root(path),
        )

    def create_directory(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.resolve(op.path or "", allow_missing=True)
        path.mkdir(parents=True, exist_ok=True)
        return FilesystemResult.ok(
            op.operation,
            message="Directory created.",
            relative_path=self.sandbox.relative_to_root(path),
        )

    def delete_file(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.resolve(op.path or "", must_be_directory=False)
        path.unlink()
        return FilesystemResult.ok(
            op.operation,
            message="File deleted.",
            relative_path=self.sandbox.relative_to_root(path),
        )

    def delete_directory(self, op: FilesystemOperation) -> FilesystemResult:
        path = self.sandbox.resolve(op.path or "", must_be_directory=True)
        if path == self.sandbox.root:
            raise OperationError("Deleting the sandbox root is forbidden.")
        shutil.rmtree(path)
        return FilesystemResult.ok(
            op.operation,
            message="Directory deleted.",
            relative_path=self.sandbox.relative_to_root(path),
        )

    def move(self, op: FilesystemOperation) -> FilesystemResult:
        source = self.sandbox.resolve(op.path or "")
        destination = self.sandbox.ensure_destination_parent(op.destination or "")
        if destination.exists():
            raise FileExistsError(destination)
        shutil.move(str(source), str(destination))
        return FilesystemResult.ok(
            op.operation,
            message="Item moved.",
            relative_path=self.sandbox.relative_to_root(destination),
        )

    def copy(self, op: FilesystemOperation) -> FilesystemResult:
        source = self.sandbox.resolve(op.path or "")
        destination = self.sandbox.ensure_destination_parent(op.destination or "")
        if destination.exists():
            raise FileExistsError(destination)

        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

        return FilesystemResult.ok(
            op.operation,
            message="Item copied.",
            relative_path=self.sandbox.relative_to_root(destination),
        )


class _SafeCalculator:
    """AST-based arithmetic evaluator; never calls eval()."""

    _binary = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _unary = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    _functions = {
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt,
        "floor": math.floor,
        "ceil": math.ceil,
    }

    def evaluate(self, expression: str) -> int | float:
        tree = ast.parse(expression, mode="eval")
        return self._node(tree.body)

    def _node(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if not math.isfinite(node.value):
                raise OperationError("Non-finite numbers are not allowed.")
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in self._binary:
            left = self._node(node.left)
            right = self._node(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise OperationError("Exponent is too large.")
            value = self._binary[type(node.op)](left, right)
            if isinstance(value, (int, float)) and not math.isfinite(value):
                raise OperationError("Calculation produced a non-finite result.")
            return value

        if isinstance(node, ast.UnaryOp) and type(node.op) in self._unary:
            return self._unary[type(node.op)](self._node(node.operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function = self._functions.get(node.func.id)
            if function is None or node.keywords:
                raise OperationError("Unsupported calculator function.")
            return function(*(self._node(arg) for arg in node.args))

        raise OperationError("Only safe arithmetic expressions are supported.")
