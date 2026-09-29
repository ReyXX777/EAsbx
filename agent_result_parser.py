from __future__ import annotations

from typing import Any

from agent_result import AgentResult


class AgentResultParser:
    """
    Converts browser-use AgentHistoryList into our application's
    stable AgentResult representation.

    No regex.
    No parsing of repr().
    No HTML.
    No UI dependencies.
    """

    @classmethod
    def parse(cls, history: Any) -> AgentResult:
        """
        Convert an AgentHistoryList into AgentResult.

        The implementation intentionally uses browser-use's public
        history API instead of inspecting its internal string format.
        """

        if history is None:
            raise ValueError("Agent history cannot be None.")

        final_text = cls._safe_call(
            history,
            "final_result",
            default=None,
        )

        is_done = cls._safe_call(
            history,
            "is_done",
            default=False,
        )

        is_successful = cls._safe_call(
            history,
            "is_successful",
            default=None,
        )

        step_count = cls._safe_call(
            history,
            "number_of_steps",
            default=0,
        )

        errors = cls._extract_errors(history)

        urls = cls._extract_urls(history)

        action_history = cls._safe_call(
            history,
            "action_history",
            default=[],
        )

        return AgentResult(
            final_text=(
                str(final_text)
                if final_text is not None
                else None
            ),
            is_done=bool(is_done),
            is_successful=is_successful,
            step_count=int(step_count or 0),
            errors=errors,
            urls=urls,
            action_history=action_history or [],
            raw_history=history,
        )

    @staticmethod
    def _safe_call(
        obj: Any,
        method_name: str,
        default: Any = None,
    ) -> Any:
        """Safely call an optional history API method."""

        method = getattr(obj, method_name, None)

        if not callable(method):
            return default

        try:
            return method()
        except Exception:
            return default

    @classmethod
    def _extract_errors(cls, history: Any) -> list[str]:
        """Extract real errors from AgentHistoryList.errors()."""

        errors = cls._safe_call(
            history,
            "errors",
            default=[],
        )

        if not errors:
            return []

        return [
            str(error)
            for error in errors
            if error
        ]

    @classmethod
    def _extract_urls(cls, history: Any) -> list[str]:
        """Extract visited URLs from AgentHistoryList.urls()."""

        urls = cls._safe_call(
            history,
            "urls",
            default=[],
        )

        if not urls:
            return []

        return [
            str(url)
            for url in urls
            if url
        ]