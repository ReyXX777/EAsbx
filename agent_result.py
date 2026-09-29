from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentResult:
    """
    Application-level representation of a completed browser-agent run.

    This is deliberately independent of Qt and UI formatting.

    browser-use owns the raw AgentHistoryList.
    This object is the stable interface our application uses.
    """

    final_text: Optional[str]

    is_done: bool
    is_successful: Optional[bool]

    step_count: int

    errors: list[str] = field(default_factory=list)

    urls: list[str] = field(default_factory=list)

    action_history: list[Any] = field(default_factory=list)

    raw_history: Any = None

    @property
    def has_errors(self) -> bool:
        """Return True when the agent reported one or more errors."""

        return bool(self.errors)

    @property
    def succeeded(self) -> bool:
        """
        Return whether the agent explicitly reported successful completion.

        This is intentionally strict. Unknown/None is not treated as success.
        """

        return self.is_done and self.is_successful is True

    @property
    def status(self) -> str:
        """Return a normalized application-level result status."""

        if not self.is_done:
            return "incomplete"

        if self.is_successful is True:
            return "completed"

        if self.is_successful is False:
            return "failed"

        return "unknown"