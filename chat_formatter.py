# chat_formatter.py
import html
import re
from datetime import datetime


class ChatMessageFormatter:
    """Single-responsibility class for parsing raw AI/User text and rendering

    industrial-grade CSS styled HTML bubbles for PySide6 QTextEdit display.
    """

    # Industrial Theme Palette
    COLOR_USER_BG = "#f4f4f5"
    COLOR_USER_BORDER = "#e4e4e7"
    COLOR_ASSISTANT_BG = "#f0f7ff"
    COLOR_ASSISTANT_BORDER = "#bfdbfe"
    COLOR_SYSTEM_BG = "#fefce8"
    COLOR_SYSTEM_BORDER = "#fef08a"
    COLOR_AGENT_BG = "#faf5ff"
    COLOR_AGENT_BORDER = "#e9d5ff"
    COLOR_ERROR_BG = "#fef2f2"
    COLOR_ERROR_BORDER = "#fecaca"

    @classmethod
    def format_message(cls, role: str, raw_text: str) -> str:
        """Formats raw input text into a styled HTML card based on the role.

        Supported roles: 'user', 'assistant', 'system', 'agent', 'error'
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        processed_body = cls._parse_markdown(raw_text)

        if role == "user":
            title = "USER"
            badge_color = "#18181b"
            bg_color = cls.COLOR_USER_BG
            border_color = cls.COLOR_USER_BORDER
        elif role == "assistant":
            title = "GEMINI AI"
            badge_color = "#2563eb"
            bg_color = cls.COLOR_ASSISTANT_BG
            border_color = cls.COLOR_ASSISTANT_BORDER
        elif role == "agent":
            title = "BROWSER AGENT"
            badge_color = "#9333ea"
            bg_color = cls.COLOR_AGENT_BG
            border_color = cls.COLOR_AGENT_BORDER
        elif role == "system":
            title = "SYSTEM"
            badge_color = "#ca8a04"
            bg_color = cls.COLOR_SYSTEM_BG
            border_color = cls.COLOR_SYSTEM_BORDER
        elif role == "error":
            title = "SYSTEM ERROR"
            badge_color = "#dc2626"
            bg_color = cls.COLOR_ERROR_BG
            border_color = cls.COLOR_ERROR_BORDER
        else:
            title = role.upper()
            badge_color = "#52525b"
            bg_color = "#ffffff"
            border_color = "#e4e4e7"

        formatted_html = f"""
        <div style="margin-bottom: 12px; background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 10px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <div style="margin-bottom: 6px; font-size: 11px;">
                <span style="background-color: {badge_color}; color: #ffffff; font-weight: bold; padding: 2px 6px; border-radius: 3px; letter-spacing: 0.5px;">{title}</span>
                <span style="color: #71717a; margin-left: 8px;">{timestamp}</span>
            </div>
            <div style="font-size: 13px; line-height: 1.5; color: #09090b;">
                {processed_body}
            </div>
        </div>
        """
        return formatted_html

    @classmethod
    def _parse_markdown(cls, text: str) -> str:
        """Lightweight Markdown and Code syntax parser to convert LLM output into

        rich HTML display format.
        """
        if not text:
            return ""

        # Escape HTML tags to prevent XSS / render corruption
        escaped_text = html.escape(text)

        # 1. Parse multi-line code blocks ```lang ... ```
        code_block_pattern = re.compile(
            r"```(?:(\w+)\n)?(.*?)```", re.DOTALL
        )

        def replace_code_block(match):
            lang = match.group(1) or "code"
            code_content = match.group(2).strip()
            return f"""
            <div style="margin: 8px 0; background-color: #1e1e2e; border-radius: 4px; border: 1px solid #313244; overflow: hidden;">
                <div style="background-color: #181825; padding: 3px 8px; font-size: 10px; color: #a6adc8; font-family: monospace; font-weight: bold; border-bottom: 1px solid #313244;">
                    {lang.upper()}
                </div>
                <pre style="margin: 0; padding: 8px; color: #cdd6f4; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; white-space: pre-wrap;">{code_content}</pre>
            </div>
            """

        escaped_text = code_block_pattern.sub(replace_code_block, escaped_text)

        # 2. Parse inline code `code`
        inline_code_pattern = re.compile(r"`([^`]+)`")
        escaped_text = inline_code_pattern.sub(
            r'<code style="background-color: #e4e4e7; color: #09090b; padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 12px;">\1</code>',
            escaped_text,
        )

        # 3. Bold **text**
        escaped_text = re.sub(
            r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped_text
        )

        # 4. Italic *text*
        escaped_text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", escaped_text)

        # 5. Convert linebreaks outside code blocks
        escaped_text = escaped_text.replace("\n", "<br>")

        return escaped_text