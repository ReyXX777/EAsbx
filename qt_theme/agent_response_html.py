from __future__ import annotations

import html

from agent_result import AgentResult

from .html import ThemeHtml


class AgentResponseParser:
    """
    Theme-aware HTML renderer for AgentResult.

    This class owns the presentation structure for agent execution results,
    while ThemeHtml owns the actual theme tokens and typography.

    It deliberately does not contain hard-coded theme colors.
    """

    @classmethod
    def parse_and_format(
        cls,
        result: AgentResult,
        theme_html: ThemeHtml,
    ) -> str:
        """
        Render an AgentResult using the supplied global HTML theme.
        """
        summary_html = cls._format_summary(result, theme_html)
        steps_html = cls._format_steps(result, theme_html)

        return f"{summary_html}\n{steps_html}"

    @classmethod
    def _format_summary(
        cls,
        result: AgentResult,
        theme_html: ThemeHtml,
    ) -> str:
        """Render the final execution result."""

        if result.final_text:
            body = cls._format_text(result.final_text, theme_html)
        else:
            body = "<div>" "No final result was returned by the agent." "</div>"

        status_label = cls._status_label(result)

        title_style = (
            f"{theme_html.title_style()} "
            f"font-size: {theme_html.small_size + 1}pt; "
            "margin-bottom: 6px;"
        )

        body_style = (
            f"{theme_html.body_style()} " f"font-size: {theme_html.small_size + 1}pt;"
        )

        return f"""
        <div style="{theme_html.success_card_style()}">
            <div style="{title_style}">
                Execution Result — {html.escape(status_label)}
            </div>

            <div style="{body_style}">
                {body}
            </div>
        </div>
        """

    @classmethod
    def _format_steps(
        cls,
        result: AgentResult,
        theme_html: ThemeHtml,
    ) -> str:
        """
        Render a collapsed execution-history scaffold.

        The detailed execution steps remain available in AgentResult,
        but are intentionally not rendered into the chat display yet.
        Interactive expansion will be implemented later at the Qt
        presentation layer.
        """

        if not result.action_history:
            return ""

        summary_style = (
            f"{theme_html.muted_style()} " "font-weight: 700; " "padding: 2px 0;"
        )

        return f"""
        <div style="
            {theme_html.elevated_card_style()}
            margin-top: 6px;
            font-size: {theme_html.small_size}pt;
        ">
            <div style="{summary_style}">
                ▸ View Agent Execution Steps
                ({result.step_count} actions)
            </div>
        </div>
        """

    @staticmethod
    def _summarize_action(step) -> str:
        """
        Produce a readable representation of one action-history entry.

        No browser-use-specific action schema is assumed here.
        """

        if isinstance(step, str):
            return step

        if isinstance(step, dict):
            action = step.get("action")

            if action is not None:
                return str(action)

            return str(step)

        return str(step)

    @staticmethod
    def _format_text(
        text: str,
        theme_html: ThemeHtml,
    ) -> str:
        """Safely format plain agent-result text."""

        escaped = html.escape(text)

        lines = escaped.splitlines()
        formatted = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("- "):
                formatted.append(
                    "<li "
                    f'style="margin-left: 15px; '
                    f'color: {theme_html.text};">'
                    f"{stripped[2:]}"
                    "</li>"
                )
            else:
                formatted.append(f"<div>{stripped}</div>")

        if not formatted:
            return ""

        return "".join(formatted)

    @staticmethod
    def _status_label(result: AgentResult) -> str:
        """Return a human-readable execution status."""

        if result.succeeded:
            return "Completed"

        if result.status == "failed":
            return "Failed"

        if result.status == "incomplete":
            return "Incomplete"

        return "Unknown"
