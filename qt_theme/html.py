from __future__ import annotations

from dataclasses import dataclass

from .palette import ThemePalette
from .typography import ThemeTypography


@dataclass(frozen=True)
class ThemeHtml:
    """
    Theme-aware HTML/CSS token provider for Qt rich-text rendering.

    ```
    Qt QTextEdit/QTextDocument supports a useful subset of HTML/CSS, but
    should not be treated as a full browser CSS engine. In particular, this
    renderer deliberately uses resolved inline CSS values instead of CSS
    custom properties such as var(--theme-text).

    The renderer is presentation-only. It does not own theme state.

    Theme state flows into this class through ThemePalette and
    ThemeTypography:

        ThemeManager
            -> ThemePalette / ThemeTypography
            -> ThemeHtml
            -> HTML formatter/parser
            -> QTextEdit/QTextDocument
    """

    palette: ThemePalette
    typography: ThemeTypography

    @classmethod
    def from_theme(
        cls,
        palette: ThemePalette,
        typography: ThemeTypography,
    ) -> "ThemeHtml":
        """
        Create an HTML theme renderer from the application's current
        global theme values.
        """
        return cls(
            palette=palette,
            typography=typography,
        )





    @property
    def font_family(self) -> str:
        """Resolved global UI font family."""
        return self.typography.family()

    @property
    def monospace_family(self) -> str:
        """Resolved global monospace font family."""
        return self.typography.monospace()

    @property
    def base_size(self) -> int:
        """Global base font size in points."""
        return self.typography.base_size

    @property
    def small_size(self) -> int:
        """Global small font size in points."""
        return self.typography.small_size

    @property
    def title_size(self) -> int:
        """Global title font size in points."""
        return self.typography.title_size





    @property
    def window(self) -> str:
        return self.palette.window

    @property
    def surface(self) -> str:
        return self.palette.surface

    @property
    def surface_alt(self) -> str:
        return self.palette.surface_alt

    @property
    def surface_elevated(self) -> str:
        return self.palette.surface_elevated

    @property
    def input(self) -> str:
        return self.palette.input

    @property
    def border(self) -> str:
        return self.palette.border

    @property
    def border_strong(self) -> str:
        return self.palette.border_strong

    @property
    def text(self) -> str:
        return self.palette.text

    @property
    def text_muted(self) -> str:
        return self.palette.text_muted

    @property
    def text_disabled(self) -> str:
        return self.palette.text_disabled

    @property
    def text_inverse(self) -> str:
        return self.palette.text_inverse

    @property
    def accent(self) -> str:
        return self.palette.accent

    @property
    def accent_hover(self) -> str:
        return self.palette.accent_hover

    @property
    def accent_pressed(self) -> str:
        return self.palette.accent_pressed

    @property
    def accent_soft(self) -> str:
        return self.palette.accent_soft

    @property
    def success(self) -> str:
        return self.palette.success

    @property
    def success_soft(self) -> str:
        return self.palette.success_soft

    @property
    def warning(self) -> str:
        return self.palette.warning

    @property
    def warning_soft(self) -> str:
        return self.palette.warning_soft

    @property
    def danger(self) -> str:
        return self.palette.danger

    @property
    def danger_soft(self) -> str:
        return self.palette.danger_soft

    @property
    def info(self) -> str:
        return self.palette.info

    @property
    def info_soft(self) -> str:
        return self.palette.info_soft

    @property
    def selection(self) -> str:
        return self.palette.selection

    @property
    def selection_text(self) -> str:
        return self.palette.selection_text

    @property
    def focus(self) -> str:
        return self.palette.focus

    @property
    def scrollbar(self) -> str:
        return self.palette.scrollbar

    @property
    def scrollbar_hover(self) -> str:
        return self.palette.scrollbar_hover

    @property
    def live(self) -> str:
        return self.palette.live

    @property
    def running(self) -> str:
        return self.palette.running

    @property
    def completed(self) -> str:
        return self.palette.completed

    @property
    def failed(self) -> str:
        return self.palette.failed

    @property
    def cancelled(self) -> str:
        return self.palette.cancelled





    def body_style(self) -> str:
        """
        Base style for ordinary conversation/result content.
        """
        return (
            f'font-family: "{self.font_family}"; '
            f"font-size: {self.base_size}pt; "
            f"line-height: 1.5; "
            f"color: {self.text};"
        )

    def muted_style(self) -> str:
        """
        Secondary/muted text style.
        """
        return (
            f'font-family: "{self.font_family}"; '
            f"font-size: {self.small_size}pt; "
            f"color: {self.text_muted};"
        )

    def title_style(self) -> str:
        """
        Global title typography.
        """
        return (
            f'font-family: "{self.font_family}"; '
            f"font-size: {self.title_size}pt; "
            f"font-weight: 700; "
            f"color: {self.text};"
        )

    def code_style(self) -> str:
        """
        Inline-code style using the global theme.
        """
        return (
            f"background-color: {self.surface_alt}; "
            f"color: {self.text}; "
            "padding: 2px 4px; "
            "border-radius: 3px; "
            f'font-family: "{self.monospace_family}"; '
            f"font-size: {self.small_size}pt;"
        )

    def code_block_style(self) -> str:
        """
        Outer style for a code block.
        """
        return (
            f"background-color: {self.surface_alt}; "
            f"border: 1px solid {self.border}; "
            "border-radius: 4px; "
            "overflow: hidden;"
        )

    def code_block_header_style(self) -> str:
        """
        Header style for a code block.
        """
        return (
            f"background-color: {self.surface_elevated}; "
            f"color: {self.text_muted}; "
            f'font-family: "{self.monospace_family}"; '
            f"font-size: {self.small_size}pt; "
            "font-weight: 700; "
            "padding: 4px 8px; "
            f"border-bottom: 1px solid {self.border};"
        )

    def code_block_content_style(self) -> str:
        """
        Content style for a code block.
        """
        return (
            f"color: {self.text}; "
            f'font-family: "{self.monospace_family}"; '
            f"font-size: {self.base_size}pt; "
            "margin: 0; "
            "padding: 8px; "
            "white-space: pre-wrap;"
        )

    def card_style(
        self,
        *,
        background: str | None = None,
        border: str | None = None,
        radius: int = 6,
        padding: str = "10px 12px",
        margin: str = "8px 0",
    ) -> str:
        """
        Generic theme-aware HTML card style.

        Callers may select semantic palette surfaces while the actual
        colors remain owned by ThemePalette.
        """
        background = background or self.surface
        border = border or self.border

        return (
            f"background-color: {background}; "
            f"border: 1px solid {border}; "
            f"border-radius: {radius}px; "
            f"padding: {padding}; "
            f"margin: {margin}; "
            f'font-family: "{self.font_family}"; '
            f"color: {self.text};"
        )

    def success_card_style(self) -> str:
        """
        Theme-aware success/result card.
        """
        return (
            f"background-color: {self.success_soft}; "
            f"border-left: 4px solid {self.success}; "
            f"color: {self.text}; "
            "padding: 10px 12px; "
            "margin: 6px 0 8px 0; "
            "border-radius: 4px;"
        )

    def elevated_card_style(self) -> str:
        """
        Theme-aware elevated information card.
        """
        return (
            f"background-color: {self.surface_elevated}; "
            f"border: 1px solid {self.border}; "
            "border-radius: 4px; "
            "padding: 6px 10px;"
        )

    def list_style(self) -> str:
        """
        Theme-aware list container style.
        """
        return (
            f"color: {self.text}; "
            f'font-family: "{self.font_family}"; '
            "margin: 8px 0 4px 18px; "
            "padding: 0;"
        )

    def step_label_style(self) -> str:
        """
        Style for secondary execution-step labels.
        """
        return f"color: {self.text_muted}; " "font-weight: 700;"

    def inline_status_style(self, status: str) -> str:
        """
        Return a semantic status color from ThemePalette.

        Unknown statuses fall back to the normal theme text color.
        """
        status_colors = {
            "live": self.live,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "success": self.success,
            "warning": self.warning,
            "danger": self.danger,
            "info": self.info,
        }

        return f"color: {status_colors.get(status.lower(), self.text)};"

    def document_style(self) -> str:
        """
        Root style for a generated HTML document/fragment.

        This is useful when an entire formatter output needs to establish
        the same theme and typography baseline.
        """
        return (
            f'font-family: "{self.font_family}"; '
            f"font-size: {self.base_size}pt; "
            f"color: {self.text}; "
            f"background-color: {self.surface}; "
            "margin: 0; "
            "padding: 0;"
        )
