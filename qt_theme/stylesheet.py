from .metrics import ResponsiveMetrics
from .palette import ThemePalette
from .typography import ThemeTypography


def build_stylesheet(
    palette: ThemePalette, typography: ThemeTypography, metrics: ResponsiveMetrics
) -> str:
    f = typography.family()
    mono = typography.monospace()
    s = metrics.spacing()
    h = metrics.control_height()
    r = metrics.radius()
    sb = metrics.px(12, 9)
    return f"""
* {{ font-family: "{f}"; font-size: {typography.base_size}pt; }}
QWidget {{ color: {palette.text}; background: {palette.window}; }}
QMainWindow, QDialog {{ background: {palette.window}; }}
QFrame, QGroupBox, QTabWidget::pane, QStackedWidget {{
    background: {palette.surface}; color: {palette.text};
}}
QGroupBox {{
    border: 1px solid {palette.border}; border-radius: {r}px;
    margin-top: 14px; padding: 10px; padding-top: 18px;
    font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QLabel {{ background: transparent; color: {palette.text}; }}
QLabel[role="muted"], QLabel.muted {{ color: {palette.text_muted}; }}
QLabel[role="title"], QLabel.title {{ font-size: {typography.title_size}pt; font-weight: 700; }}
QLabel[role="metric"], QLabel.metric {{ font-size: {typography.metric_size}pt; font-weight: 700; }}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox,
QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {{
    background: {palette.input}; color: {palette.text};
    border: 1px solid {palette.border}; border-radius: {r}px;
    selection-background-color: {palette.selection};
    selection-color: {palette.selection_text};
    min-height: {h}px; padding: 2px {s}px;
}}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {palette.border_strong};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {palette.focus};
}}
QComboBox QAbstractItemView {{
    background: {palette.surface_elevated}; color: {palette.text};
    border: 1px solid {palette.border};
    selection-background-color: {palette.selection};
    selection-color: {palette.selection_text};
}}
QPushButton, QToolButton {{
    background: {palette.surface_alt}; color: {palette.text};
    border: 1px solid {palette.border}; border-radius: {r}px;
    min-height: {h}px; padding: 0 {s + 4}px;
}}
QPushButton:hover, QToolButton:hover {{
    background: {palette.accent_soft}; border-color: {palette.accent};
}}
QPushButton:pressed, QToolButton:pressed {{
    background: {palette.accent}; color: {palette.text_inverse};
}}
QPushButton:disabled, QToolButton:disabled {{
    color: {palette.text_disabled}; background: {palette.surface_alt};
}}
QPushButton[role="primary_action"], QPushButton.primary_action {{
    background: {palette.accent}; color: {palette.text_inverse};
    border-color: {palette.accent};
}}
QPushButton[role="danger"], QPushButton.danger {{
    background: {palette.danger}; color: {palette.text_inverse};
    border-color: {palette.danger};
}}
QPushButton[role="secondary_action"], QPushButton.secondary_action {{
    background: {palette.surface_alt}; color: {palette.text};
    border-color: {palette.border};
}}
QPushButton[role="icon_button"], QPushButton.icon_button {{
    background: transparent; color: {palette.text};
    border: 1px solid transparent; border-radius: {r}px;
    padding: 0;
}}
QPushButton[role="icon_button"]:hover {{
    background: {palette.accent_soft}; border-color: {palette.accent};
}}
QPushButton[role="icon_button"]:pressed {{
    background: {palette.accent}; color: {palette.text_inverse};
}}
QCheckBox, QRadioButton {{ background: transparent; color: {palette.text}; spacing: {s}px; }}
QListWidget, QTreeWidget, QTableWidget, QTableView {{
    background: {palette.surface}; alternate-background-color: {palette.surface_alt};
    color: {palette.text}; border: 1px solid {palette.border};
    gridline-color: {palette.border};
    selection-background-color: {palette.selection};
    selection-color: {palette.selection_text}; outline: none;
}}
QListWidget::item, QTreeWidget::item {{ padding: 4px {s}px; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {palette.surface_alt}; }}
QHeaderView::section {{
    background: {palette.surface_alt}; color: {palette.text};
    border: none; border-bottom: 1px solid {palette.border};
    padding: 4px {s}px; font-weight: 600;
}}
QScrollBar:vertical {{ background: {palette.surface_alt}; width: {sb}px; }}
QScrollBar::handle:vertical {{
    background: {palette.scrollbar}; min-height: 24px; border-radius: 6px;
}}
QScrollBar::handle:vertical:hover {{ background: {palette.scrollbar_hover}; }}
QScrollBar:horizontal {{ background: {palette.surface_alt}; height: {sb}px; }}
QScrollBar::handle:horizontal {{
    background: {palette.scrollbar}; min-width: 24px; border-radius: 6px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ background: transparent; border: none; }}
QTabWidget::pane {{ border: 1px solid {palette.border}; }}
QTabBar::tab {{
    background: {palette.surface_alt}; color: {palette.text_muted};
    border: 1px solid transparent; padding: 4px {s + 2}px;
    min-height: {metrics.compact_control_height()}px;
}}
QTabBar::tab:hover {{ color: {palette.text}; background: {palette.surface}; }}
QTabBar::tab:selected {{
    color: {palette.text}; background: {palette.surface};
    border-bottom: 2px solid {palette.accent};
}}
QMenuBar {{ background: {palette.surface}; color: {palette.text}; border-bottom: 1px solid {palette.border}; }}
QMenuBar::item:selected, QMenu::item:selected {{
    background: {palette.selection}; color: {palette.selection_text};
}}
QMenu {{ background: {palette.surface_elevated}; color: {palette.text}; border: 1px solid {palette.border}; }}
QMenu::item {{ padding: 4px {s + 8}px; }}
QStatusBar {{ background: {palette.surface_alt}; color: {palette.text_muted}; }}
QSplitter::handle {{ background: {palette.border}; }}
QSplitter::handle:hover {{ background: {palette.border_strong}; }}
QToolTip {{
    background: {palette.surface_elevated}; color: {palette.text};
    border: 1px solid {palette.border_strong}; padding: 4px 8px;
}}
QTextEdit, QPlainTextEdit {{ font-family: "{mono}"; }}
QTextEdit[role="conversation_display"] {{
    background: {palette.surface};
    color: {palette.text};
    border: none;
}}
QWebEngineView {{ background: {palette.surface}; }}
QFrame[role="panel"], QWidget[role="panel"] {{
    background: {palette.surface}; border: 1px solid {palette.border};
}}
QFrame[role="sidebar"], QWidget[role="sidebar"] {{
    background: {palette.surface_alt}; border-right: 1px solid {palette.border};
}}

QFrame#chatHeader {{
    background: {palette.surface};
    color: {palette.text};
    border-bottom: 1px solid {palette.border};
}}

QLabel#agentIcon {{
    background: {palette.accent_soft};
    color: {palette.accent};
    border: 1px solid {palette.border};
    border-radius: {r}px;
    font-weight: 700;
}}

QLabel[role="status_indicator"] {{
    background: transparent;
    border: none;
    font-weight: 700;
}}

QLabel[status="live"] {{ color: {palette.live}; }}
QLabel[status="running"] {{ color: {palette.running}; }}
QLabel[status="completed"] {{ color: {palette.completed}; }}
QLabel[status="failed"] {{ color: {palette.failed}; }}
QLabel[status="cancelled"] {{ color: {palette.cancelled}; }}

QFrame[role="composer"] {{
    background: {palette.surface};
    color: {palette.text};
    border-top: 1px solid {palette.border};
}}

QFrame#inputCard {{
    background: {palette.input};
    color: {palette.text};
    border: 1px solid {palette.border};
    border-radius: {r}px;
}}

QWidget#approvalContainer {{
    background: {palette.surface};
    color: {palette.text};
}}

QTableCornerButton::section {{ background: {palette.surface_alt}; border: 1px solid {palette.border}; }}
""".strip()
