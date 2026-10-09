from __future__ import annotations

import os
from pathlib import Path

from .filesystem_validator import FilesystemInputValidator, ValidationError


class SandboxViolation(PermissionError):
    """Raised when an operation attempts to leave the configured sandbox."""


class SandboxValidator:
    """
    Security boundary for all filesystem operations.

    The caller only supplies paths relative to `root`.
    Every path is normalized and resolved before it is returned.
    """

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise NotADirectoryError(f"Sandbox root is not a directory: {self.root}")

    def relative(self, value: str) -> str:
        return FilesystemInputValidator.relative_path(value)

    def resolve(
        self,
        relative_path: str,
        *,
        allow_missing: bool = False,
        must_be_directory: bool | None = None,
    ) -> Path:
        try:
            normalized = self.relative(relative_path)
        except ValidationError as exc:
            raise SandboxViolation(str(exc)) from exc

        candidate = self.root / normalized
        try:
            resolved = candidate.resolve(strict=not allow_missing)
        except FileNotFoundError:
            if not allow_missing:
                raise

            resolved = candidate.parent.resolve(strict=True) / candidate.name

        self._assert_contained(resolved)

        if must_be_directory is True and resolved.exists() and not resolved.is_dir():
            raise NotADirectoryError(resolved)
        if must_be_directory is False and resolved.exists() and not resolved.is_file():
            raise IsADirectoryError(resolved)

        return resolved

    def _assert_contained(self, candidate: Path) -> None:
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise SandboxViolation(
                f"Path escapes sandbox root: {candidate}"
            ) from exc

    def relative_to_root(self, path: Path) -> str:
        resolved = path.resolve(strict=False)
        self._assert_contained(resolved)
        relative = resolved.relative_to(self.root)
        return relative.as_posix() or "."

    def ensure_destination_parent(self, relative_path: str) -> Path:
        target = self.resolve(relative_path, allow_missing=True)
        target.parent.mkdir(parents=True, exist_ok=True)

        parent = target.parent.resolve(strict=True)
        self._assert_contained(parent)
        return target
