from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FilesystemToolActivity:
    """
    Provider-neutral description of one filesystem-agent tool activity.

    This model is used to communicate agent execution activity
    from the execution layer toward observers such as the UI.

    It intentionally has no Qt dependency.
    """

    tool_name: str
    arguments: dict[str, Any]

    @property
    def path(self) -> str | None:
        """
        Return the sandbox-relative path associated with this
        tool activity, when one exists.
        """

        path = self.arguments.get("path")

        if path is None:
            return None

        return str(path)

    @property
    def is_navigation(self) -> bool:
        """
        Whether this activity represents directory navigation/
        inspection that can be visualized in FilesWorkspace.
        """

        return self.tool_name == "list_directory"

    @property
    def is_file_access(self) -> bool:
        """
        Whether this activity represents opening/reading a file.
        """

        return self.tool_name in {
            "read_file",
            "read_table",
        }
