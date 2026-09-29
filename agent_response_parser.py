from __future__ import annotations

import html

from agent_result import AgentResult


class AgentResponseParser:
    """
    Converts an AgentResult into safe HTML for the chat UI.

    Important:
    This class does NOT understand browser-use internals.

    AgentResult is the boundary between execution and presentation.
    """

    @classmethod
    def parse_and_format(
        cls,
        result: AgentResult,
    ) -> str:
        """
        Render an AgentResult into the execution-result HTML block.
        """

        summary_html = cls._format_summary(result)

        steps_html = cls._format_steps(result)

        return f"{summary_html}\n{steps_html}"

    @classmethod
    def _format_summary(
        cls,
        result: AgentResult,
    ) -> str:
        """Render the final result."""

        if result.final_text:
            body = cls._format_text(result.final_text)
        else:
            body = (
                "<div>No final result was returned by the agent.</div>"
            )

        status_label = cls._status_label(result)

        return f"""
        <div style="
            background-color: #f8fafc;
            border-left: 4px solid #16a34a;
            padding: 10px 12px;
            margin-top: 6px;
            margin-bottom: 8px;
            border-radius: 4px;
        ">
            <div style="
                font-weight: bold;
                color: #1e293b;
                font-size: 13px;
                margin-bottom: 6px;
            ">
                📌 Execution Result — {status_label}
            </div>

            <div style="
                font-size: 13px;
                color: #334155;
                line-height: 1.5;
            ">
                {body}
            </div>
        </div>
        """

    @classmethod
    def _format_steps(
        cls,
        result: AgentResult,
    ) -> str:
        """Render the actual browser-use action history."""

        if not result.action_history:
            return ""

        items = []

        for index, step in enumerate(
            result.action_history,
            start=1,
        ):
            details = html.escape(
                cls._summarize_action(step)
            )

            items.append(
                f"""
                <li style="margin-bottom: 4px;">
                    <strong style="color: #64748b;">
                        Step {index}:
                    </strong>
                    <code>{details}</code>
                </li>
                """
            )

        steps_html = "".join(items)

        return f"""
        <details style="
            margin-top: 6px;
            background-color: #f1f5f9;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        ">
            <summary style="
                font-weight: bold;
                color: #475569;
                cursor: pointer;
                user-select: none;
            ">
                🔍 View Agent Execution Steps
                ({result.step_count} actions)
            </summary>

            <ul style="
                margin: 8px 0 4px 18px;
                padding: 0;
                color: #334155;
                font-family: monospace;
            ">
                {steps_html}
            </ul>
        </details>
        """

    @staticmethod
    def _summarize_action(step) -> str:
        """
        Produce a readable representation of one action-history entry.

        We deliberately do not assume a specific action schema here.
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
    def _format_text(text: str) -> str:
        """Safely format plain agent result text."""

        escaped = html.escape(text)

        lines = escaped.splitlines()

        formatted = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("- "):
                formatted.append(
                    f"<li style='margin-left: 15px;'>"
                    f"{stripped[2:]}"
                    f"</li>"
                )
            else:
                formatted.append(
                    f"<div>{stripped}</div>"
                )

        return "".join(formatted)

    @staticmethod
    def _status_label(result: AgentResult) -> str:
        """Return a human-readable status."""

        if result.succeeded:
            return "Completed"

        if result.status == "failed":
            return "Failed"

        if result.status == "incomplete":
            return "Incomplete"

        return "Unknown"