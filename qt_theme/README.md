# MOCKAPP Qt Theme

Target location: `X:\MOCKAPP\qt_theme\`

## Public API

```python
from qt_theme import ThemeManager, ThemeMode

ThemeManager.instance().apply(app, ThemeMode.SYSTEM)
```

Modes:
- `ThemeMode.LIGHT`
- `ThemeMode.DARK`
- `ThemeMode.SYSTEM`

Runtime switching:
```python
manager = ThemeManager.instance()
manager.set_mode(ThemeMode.DARK)
manager.toggle()
```

The package covers the inventory's major visual Qt surface: QWidget,
QFrame, QGroupBox, QMainWindow, QStackedWidget, QTabWidget/QTabBar,
QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, buttons,
checkbox/radio controls, list/tree/table views, headers, scrollbars,
menus, status bars, splitters, tooltips, message boxes and the
QWebEngineView host.

### Important

The inventory reports many existing `setStyleSheet()` calls and hard-coded
hex colors in MOCKAPP. Those local rules can override the global theme.
They must be migrated component-by-component; the global package should
not blindly delete them.

`QWebEngineView` itself is themed, but HTML rendered inside the browser is
owned by the webpage and needs its own CSS/theme bridge if browser-page
dark mode is desired.

### Semantic roles

Use dynamic properties instead of hard-coded colors:

```python
button.setProperty("role", "primary")
label.setProperty("role", "muted")
panel.setProperty("role", "panel")
sidebar.setProperty("role", "sidebar")
status.setProperty("status", "completed")
```

Then repolish the widget if the property changes at runtime.

### Fonts

The preference order favors Noto Sans and Noto CJK/Devanagari families,
then Segoe UI/Arial/Qt Sans Serif. No font is downloaded or assumed to be
installed.

### Responsive behavior

`ResponsiveMetrics.for_widget(widget)` accounts for logical DPI and broad
window width. Qt layouts remain responsible for the actual geometry.
Avoid hard-coded global widths in the main window, chat, browser and
observation monitor.
