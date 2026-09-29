# agent_response_parser.py
import html
import re
from typing import Dict, List, Tuple


class AgentResponseParser:
    """Predictive parsing engine for browser-use agent outputs."""

    @classmethod
    def parse_and_format(cls, raw_result_str: str) -> str:
        """Parses raw AgentHistoryList string or plain text into formatted HTML

        with cascading styles and collapsible step logs.
        """
        final_summary, extracted_steps = cls._extract_semantics(raw_result_str)

        # 1. Format the main output card
        formatted_summary = cls._format_summary_card(final_summary)

        # 2. Format step telemetry into a collapsible HTML block
        formatted_steps = cls._format_collapsible_steps(extracted_steps)

        return f"{formatted_summary}\n{formatted_steps}"

    @classmethod
    def _extract_semantics(
        cls, raw_str: str
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Predictively extracts final outcome and intermediate execution steps."""
        steps = []
        final_summary = ""

        # Regex patterns to capture intermediate ActionResults
        action_pattern = re.compile(
            r"ActionResult\([^)]*?extracted_content=['\"](.*?)['\"]", re.DOTALL
        )
        for match in action_pattern.finditer(raw_str):
            try:
                content = match.group(1).encode("utf-8").decode("unicode_escape")
            except Exception:
                content = match.group(1)

            if content.strip() and not content.startswith("Match:"):
                clean_content = (
                    content[:120] + "..." if len(content) > 120 else content
                )
                steps.append(
                    {"type": "Action / DOM Step", "details": clean_content}
                )

        # Pattern for final text inside done(...)
        done_pattern = re.compile(
            r"done=['\"]?\{'text':\s*['\"](.*?)['\"]", re.DOTALL
        )
        done_match = done_pattern.search(raw_str)

        if done_match:
            try:
                final_summary = (
                    done_match.group(1)
                    .encode("utf-8")
                    .decode("unicode_escape")
                )
            except Exception:
                final_summary = done_match.group(1)
        else:
            # Fallback for extracted content near end of response
            summary_pattern = re.compile(
                r"extracted_content=['\"](Match:[^'\"]+)['\"]", re.DOTALL
            )
            summary_match = summary_pattern.search(raw_str)
            if summary_match:
                final_summary = summary_match.group(1)
            else:
                final_summary = raw_str

        return final_summary, steps

    @classmethod
    def _format_summary_card(cls, text: str) -> str:
        """Renders the main agent output inside a visual CSS container."""
        if not text:
            text = "Task executed successfully with no returned text."

        # Escape HTML characters first to prevent XSS/broken layout
        text_escaped = html.escape(text)

        # Convert simple markdown to HTML inside summary card
        # Bold
        text_escaped = re.sub(
            r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text_escaped
        )

        # Bullets (- Item)
        lines = text_escaped.split("\n")
        formatted_lines = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("- ") or line_str.startswith("* "):
                formatted_lines.append(
                    f"<li style='margin-left: 15px;'>{line_str[2:]}</li>"
                )
            elif line_str:
                formatted_lines.append(f"<div>{line_str}</div>")

        processed_body = "".join(formatted_lines)

        return f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #16a34a; padding: 10px 12px; margin-top: 6px; margin-bottom: 8px; border-radius: 4px;">
            <div style="font-weight: bold; color: #1e293b; font-size: 13px; margin-bottom: 6px;">📌 Execution Result</div>
            <div style="font-size: 13px; color: #334155; line-height: 1.5;">{processed_body}</div>
        </div>
        """

    @classmethod
    def _format_collapsible_steps(cls, steps: List[Dict[str, str]]) -> str:
        """Generates an HTML details/summary collapsible dropdown for agent steps."""
        if not steps:
            return ""

        step_items_html = ""
        for idx, step in enumerate(steps, 1):
            clean_details = html.escape(step["details"])
            step_items_html += f"""
            <li style="margin-bottom: 4px;">
                <strong style="color: #64748b;">Step {idx}:</strong> <code>{clean_details}</code>
            </li>
            """

        return f"""
        <details style="margin-top: 6px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px 10px; font-size: 12px;">
            <summary style="font-weight: bold; color: #475569; cursor: pointer; user-select: none;">
                🔍 View Agent Execution Steps ({len(steps)} actions)
            </summary>
            <ul style="margin: 8px 0 4px 18px; padding: 0; color: #334155; font-family: monospace;">
                {step_items_html}
            </ul>
        </details>
        """