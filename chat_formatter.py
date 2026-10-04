import html
import re
from datetime import datetime

from qt_theme import ThemeManager


class ChatMessageFormatter:
    """Single-responsibility formatter for rendering chat messages as
    theme-aware HTML suitable for PySide6 QTextEdit/QTextBrowser display.

    All colors and typography are obtained from the global MOCKAPP Qt theme.
    No local light/dark palette is maintained here.
    """

    @classmethod
    def _theme(cls):
        """Return the active global theme manager."""
        return ThemeManager.instance()

    @classmethod
    def format_message(cls, role: str, raw_text: str) -> str:
        """Format raw input text into a theme-aware HTML chat card.

        Supported roles:
            user
            assistant
            system
            agent
            error

        The generated HTML intentionally uses the active global Qt theme
        palette and typography rather than hard-coded colors.
        """
        theme = cls._theme()
        palette = theme.palette
        typography = theme.typography

        timestamp = datetime.now().strftime("%H:%M:%S")
        processed_body = cls._parse_markdown(raw_text)

        if role == "user":
            title = "USER"
            badge_color = palette.text
            bg_color = palette.surface_alt
            border_color = palette.border

        elif role == "assistant":
            title = "GEMINI AI"
            badge_color = palette.accent
            bg_color = palette.accent_soft
            border_color = palette.border

        elif role == "agent":
            title = "BROWSER AGENT"
            badge_color = palette.accent
            bg_color = palette.accent_soft
            border_color = palette.border

        elif role == "system":
            title = "SYSTEM"
            badge_color = palette.warning
            bg_color = palette.warning_soft
            border_color = palette.border

        elif role == "error":
            title = "SYSTEM ERROR"
            badge_color = palette.danger
            bg_color = palette.danger_soft
            border_color = palette.danger

        else:
            title = role.upper()
            badge_color = palette.text_muted
            bg_color = palette.surface_alt
            border_color = palette.border

        base_size = typography.base_size
        mono = typography.monospace()

        formatted_html = f"""
        <div style="
            margin-bottom: 12px;
            background-color: {bg_color};
            color: {palette.text};
            border: 1px solid {border_color};
            border-radius: 6px;
            padding: 10px 12px;
            font-family: '{typography.family()}';
            font-size: {base_size}pt;
        ">
            <div style="
                margin-bottom: 7px;
                font-size: {typography.small_size}pt;
            ">
                <span style="
                    background-color: {badge_color};
                    color: {palette.text_inverse};
                    font-weight: bold;
                    padding: 2px 6px;
                    border-radius: 3px;
                    letter-spacing: 0.5px;
                ">{title}</span>

                <span style="
                    color: {palette.text_muted};
                    margin-left: 8px;
                ">{timestamp}</span>
            </div>

            <div style="
                font-size: {base_size}pt;
                line-height: 1.55;
                color: {palette.text};
            ">
                {processed_body}
            </div>
        </div>
        """

        return formatted_html

    @classmethod
    def _parse_markdown(cls, text: str) -> str:
        """Convert lightweight Markdown and code syntax into theme-aware HTML.

        HTML input is escaped before Markdown processing so raw model output
        cannot corrupt the QTextEdit rich-text document.
        """
        if not text:
            return ""

        theme = cls._theme()
        palette = theme.palette
        typography = theme.typography
        mono = typography.monospace()

        # Escape HTML tags to prevent XSS / render corruption.
        escaped_text = html.escape(text)

        # ------------------------------------------------------------------
        # 1. Multi-line code blocks
        # ------------------------------------------------------------------
        code_block_pattern = re.compile(
            r"```(?:(\w+)\n)?(.*?)```",
            re.DOTALL,
        )

        def replace_code_block(match):
            lang = match.group(1) or "code"
            code_content = match.group(2).strip()

            return f"""
            <div style="
                margin: 8px 0;
                background-color: {palette.surface_elevated};
                color: {palette.text};
                border-radius: 4px;
                border: 1px solid {palette.border};
                overflow: hidden;
            ">
                <div style="
                    background-color: {palette.surface_alt};
                    padding: 4px 8px;
                    font-size: {typography.small_size}pt;
                    color: {palette.text_muted};
                    font-family: '{mono}';
                    font-weight: bold;
                    border-bottom: 1px solid {palette.border};
                ">
                    {lang.upper()}
                </div>

                <pre style="
                    margin: 0;
                    padding: 9px;
                    color: {palette.text};
                    background-color: {palette.surface_elevated};
                    font-family: '{mono}';
                    font-size: {typography.base_size}pt;
                    white-space: pre-wrap;
                ">{code_content}</pre>
            </div>
            """

        escaped_text = code_block_pattern.sub(
            replace_code_block,
            escaped_text,
        )

        # ------------------------------------------------------------------
        # 2. Inline code
        # ------------------------------------------------------------------
        inline_code_pattern = re.compile(r"`([^`]+)`")

        inline_code_html = (
            f'<code style="'
            f"background-color: {palette.surface_alt}; "
            f"color: {palette.text}; "
            f"padding: 2px 4px; "
            f"border-radius: 3px; "
            f"border: 1px solid {palette.border}; "
            f"font-family: '{mono}'; "
            f"font-size: {typography.base_size}pt;"
            f'">\\1</code>'
        )

        escaped_text = inline_code_pattern.sub(
            inline_code_html,
            escaped_text,
        )

        # ------------------------------------------------------------------
        # 3. Bold
        # ------------------------------------------------------------------
        escaped_text = re.sub(
            r"\*\*(.*?)\*\*",
            r"<strong>\1</strong>",
            escaped_text,
        )

        # ------------------------------------------------------------------
        # 4. Italic
        # ------------------------------------------------------------------
        escaped_text = re.sub(
            r"\*(.*?)\*",
            r"<em>\1</em>",
            escaped_text,
        )

        # ------------------------------------------------------------------
        # 5. Convert line breaks
        # ------------------------------------------------------------------
        escaped_text = escaped_text.replace(
            "\n",
            "<br>",
        )

        return escaped_text
