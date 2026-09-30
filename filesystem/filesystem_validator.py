from __future__ import annotations

import re
from pathlib import Path


class ValidationError(ValueError):
    """Raised when a filesystem argument is invalid before I/O occurs."""


class FilesystemInputValidator:
    """Pure input validation; contains no filesystem access."""

    _SAFE_ENCODINGS = {"utf-8", "utf-8-sig", "utf-16", "ascii", "latin-1"}

    @classmethod
    def relative_path(cls, value: str, *, field_name: str = "path") -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field_name} must be a non-empty string.")

        value = value.replace("\\", "/").strip()

        if "\x00" in value:
            raise ValidationError(f"{field_name} contains a NUL character.")

        # Absolute Windows paths, UNC paths, and URI-like paths are forbidden.
        if value.startswith(("/", "//", "\\\\")) or re.match(r"^[A-Za-z]:", value):
            raise ValidationError(
                f"{field_name} must be sandbox-relative, not an absolute path."
            )

        # Reject traversal before the path reaches the OS.
        parts = [part for part in value.split("/") if part not in ("", ".")]
        if any(part == ".." for part in parts):
            raise ValidationError(f"{field_name} contains parent traversal ('..').")

        return "/".join(parts) or "."

    @classmethod
    def pattern(cls, value: str | None) -> str:
        if value is None or value == "":
            return "*"
        if "\x00" in value:
            raise ValidationError("pattern contains a NUL character.")
        return value

    @classmethod
    def encoding(cls, value: str) -> str:
        if value.lower() not in cls._SAFE_ENCODINGS:
            raise ValidationError(f"Encoding is not allowed: {value}")
        return value.lower()

    @classmethod
    def text_query(cls, value: str | None) -> str:
        if value is None:
            return ""
        if "\x00" in value:
            raise ValidationError("query contains a NUL character.")
        return value

    @classmethod
    def expression(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("expression must be a non-empty string.")
        if len(value) > 2000:
            raise ValidationError("expression is too long.")
        return value.strip()
