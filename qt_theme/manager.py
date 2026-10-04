from PySide6.QtCore import QObject, QEvent, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QWidget
from .metrics import ResponsiveMetrics
from .mode import ThemeMode
from .palette import ThemePalette, palette_for_dark
from .stylesheet import build_stylesheet
from .system import system_prefers_dark
from .typography import ThemeTypography

class _ThemeEventFilter(QObject):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.ApplicationPaletteChange, QEvent.Type.Polish, QEvent.Type.Show):
            if isinstance(watched, QWidget):
                self.manager.refresh_widget(watched)
        return False

class ThemeManager(QObject):
    theme_changed = Signal(str)
    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = ThemeMode.SYSTEM
        self._dark = False
        self._palette = palette_for_dark(False)
        self._typography = ThemeTypography()
        self._event_filter = _ThemeEventFilter(self)
        self._app = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def mode(self): return self._mode
    @property
    def dark(self): return self._dark
    @property
    def palette(self) -> ThemePalette: return self._palette
    @property
    def typography(self): return self._typography

    def apply(self, app: QApplication, mode=ThemeMode.SYSTEM):
        self._app = app
        self.set_mode(mode, emit=False)
        app.installEventFilter(self._event_filter)
        app.setFont(self._typography.base_font())
        app.setPalette(self._build_palette())
        self._apply_stylesheet()

    def set_mode(self, mode, *, emit=True):
        if isinstance(mode, str):
            mode = ThemeMode(mode.lower())
        self._mode = mode
        self._dark = system_prefers_dark() if mode is ThemeMode.SYSTEM else mode is ThemeMode.DARK
        self._palette = palette_for_dark(self._dark)
        if self._app is not None:
            self._app.setFont(self._typography.base_font())
            self._app.setPalette(self._build_palette())
            self._apply_stylesheet()
        if emit:
            self.theme_changed.emit(self._mode.value)

    def toggle(self):
        self.set_mode(ThemeMode.LIGHT if self._dark else ThemeMode.DARK)

    def refresh_system_theme(self):
        if self._mode is ThemeMode.SYSTEM:
            self.set_mode(ThemeMode.SYSTEM)

    def refresh_widget(self, widget: QWidget):
        metrics = ResponsiveMetrics.for_widget(widget)
        widget.setProperty("themeScale", metrics.scale)
        widget.setProperty("themeControlHeight", metrics.control_height())
        if widget.style():
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        widget.update()

    def _apply_stylesheet(self):
        if self._app is not None:
            self._app.setStyleSheet(
                build_stylesheet(self._palette, self._typography, ResponsiveMetrics())
            )

    def _build_palette(self):
        p = self._palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, p.window)
        palette.setColor(QPalette.ColorRole.Base, p.input)
        palette.setColor(QPalette.ColorRole.AlternateBase, p.surface_alt)
        palette.setColor(QPalette.ColorRole.Text, p.text)
        palette.setColor(QPalette.ColorRole.WindowText, p.text)
        palette.setColor(QPalette.ColorRole.Button, p.surface_alt)
        palette.setColor(QPalette.ColorRole.ButtonText, p.text)
        palette.setColor(QPalette.ColorRole.Highlight, p.selection)
        palette.setColor(QPalette.ColorRole.HighlightedText, p.selection_text)
        palette.setColor(QPalette.ColorRole.ToolTipBase, p.surface_elevated)
        palette.setColor(QPalette.ColorRole.ToolTipText, p.text)
        return palette
