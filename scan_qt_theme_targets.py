from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path










PROJECT_ROOT = Path(__file__).resolve().parent



















TARGET_FILES: list[str] = [
    "observation_widget.py",
]



OUTPUT_FILE = PROJECT_ROOT / "MOCKAPP_QT_THEME_MIGRATION_REPORT.txt"






EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


QT_ROOTS = {
    "PySide6",
    "PyQt6",
    "PySide2",
    "PyQt5",
}









KNOWN_QT_COMPONENTS = {

    "QApplication",
    "QGuiApplication",
    "QCoreApplication",
    "QObject",
    "QEvent",
    "QTimer",
    "QThread",
    "QThreadPool",
    "QRunnable",

    "QWidget",
    "QMainWindow",
    "QDialog",
    "QDialogButtonBox",
    "QDockWidget",
    "QMdiArea",
    "QMdiSubWindow",
    "QScrollArea",
    "QStackedWidget",
    "QStackedLayout",
    "QTabWidget",
    "QFrame",
    "QGroupBox",
    "QSplitter",

    "QLayout",
    "QBoxLayout",
    "QVBoxLayout",
    "QHBoxLayout",
    "QGridLayout",
    "QFormLayout",

    "QLabel",
    "QTextBrowser",
    "QTextEdit",
    "QPlainTextEdit",
    "QLCDNumber",
    "QProgressBar",
    "QCalendarWidget",

    "QPushButton",
    "QToolButton",
    "QRadioButton",
    "QCheckBox",
    "QCommandLinkButton",
    "QAbstractButton",
    "QAction",
    "QActionGroup",

    "QLineEdit",
    "QComboBox",
    "QSpinBox",
    "QDoubleSpinBox",
    "QDateEdit",
    "QDateTimeEdit",
    "QTimeEdit",
    "QSlider",
    "QDial",
    "QKeySequenceEdit",

    "QListWidget",
    "QListWidgetItem",
    "QListView",
    "QTreeWidget",
    "QTreeWidgetItem",
    "QTreeView",
    "QTableWidget",
    "QTableWidgetItem",
    "QTableView",
    "QAbstractItemView",
    "QHeaderView",

    "QTabBar",
    "QToolBar",
    "QMenuBar",
    "QMenu",
    "QStatusBar",

    "QMessageBox",
    "QFileDialog",
    "QColorDialog",
    "QFontDialog",
    "QInputDialog",
    "QProgressDialog",
    "QErrorMessage",

    "QScrollBar",
    "QAbstractScrollArea",

    "QPainter",
    "QPaintEvent",
    "QPen",
    "QBrush",
    "QColor",
    "QFont",
    "QFontMetrics",
    "QPixmap",
    "QImage",
    "QIcon",
    "QPalette",
    "QCursor",

    "QModelIndex",
    "QAbstractItemModel",
    "QAbstractListModel",
    "QAbstractTableModel",
    "QStandardItemModel",
    "QStandardItem",
    "QItemSelectionModel",
    "QSortFilterProxyModel",

    "QScreen",
    "QWindow",
    "QSystemTrayIcon",
    "QClipboard",

    "QWebEngineView",
    "QWebEnginePage",
    "QWebEngineProfile",
    "QWebEngineSettings",
    "QWebEngineDownloadRequest",
    "QWebEngineFullScreenRequest",
    "QWebChannel",
}






THEME_METHODS = {
    "setStyleSheet",
    "setPalette",
    "setFont",
    "setObjectName",
    "setProperty",
    "setMinimumHeight",
    "setMaximumHeight",
    "setFixedHeight",
    "setMinimumWidth",
    "setMaximumWidth",
    "setFixedWidth",
    "resize",
    "setMinimumSize",
    "setMaximumSize",
    "setFixedSize",
    "setContentsMargins",
    "setSpacing",
    "setStyle",
    "setAutoFillBackground",
    "setFrameShape",
    "setFrameShadow",
    "setLineWidth",
    "setIconSize",
    "setIcon",
    "setPlaceholderText",
    "setReadOnly",
    "setEnabled",
    "setDisabled",
    "setVisible",
    "hide",
    "show",
    "setProperty",
}






STYLE_PATTERNS = {
    "hex color": re.compile(r"#[0-9a-fA-F]{3,8}\b"),
    "rgb/rgba color": re.compile(
        r"\brgba?\s*\(",
        re.IGNORECASE,
    ),
    "setStyleSheet": re.compile(r"\.setStyleSheet\s*\("),
    "setPalette": re.compile(r"\.setPalette\s*\("),
    "QColor": re.compile(r"\bQColor\s*\("),
    "font-size": re.compile(r"\bfont-size\s*:"),
    "font-family": re.compile(r"\bfont-family\s*:"),
    "background": re.compile(r"\bbackground(?:-color)?\s*:"),
    "foreground/color": re.compile(r"\bcolor\s*:"),
    "border": re.compile(r"\bborder(?:-[a-z]+)?\s*:"),
    "border-radius": re.compile(r"\bborder-radius\s*:"),
    "padding": re.compile(r"\bpadding(?:-[a-z]+)?\s*:"),
    "margin": re.compile(r"\bmargin(?:-[a-z]+)?\s*:"),
    "min-height": re.compile(r"\bmin-height\s*:"),
    "min-width": re.compile(r"\bmin-width\s*:"),
}













THEME_VOCABULARY = {
    "surface": "palette.surface",
    "surface_alt": "palette.surface_alt",
    "surface_elevated": "palette.surface_elevated",
    "window": "palette.window",
    "input": "palette.input",
    "border": "palette.border",
    "border_strong": "palette.border_strong",
    "text": "palette.text",
    "text_muted": "palette.text_muted",
    "text_disabled": "palette.text_disabled",
    "text_inverse": "palette.text_inverse",
    "accent": "palette.accent",
    "accent_hover": "palette.accent_hover",
    "accent_pressed": "palette.accent_pressed",
    "accent_soft": "palette.accent_soft",
    "success": "palette.success",
    "success_soft": "palette.success_soft",
    "warning": "palette.warning",
    "warning_soft": "palette.warning_soft",
    "danger": "palette.danger",
    "danger_soft": "palette.danger_soft",
    "info": "palette.info",
    "info_soft": "palette.info_soft",
    "selection": "palette.selection",
    "selection_text": "palette.selection_text",
    "focus": "palette.focus",
    "scrollbar": "palette.scrollbar",
    "scrollbar_hover": "palette.scrollbar_hover",
    "live": "palette.live",
    "running": "palette.running",
    "completed": "palette.completed",
    "failed": "palette.failed",
    "cancelled": "palette.cancelled",
    "panel": 'widget.setProperty("role", "panel")',
    "sidebar": 'widget.setProperty("role", "sidebar")',
    "muted": 'widget.setProperty("role", "muted")',
    "title": 'widget.setProperty("role", "title")',
    "metric": 'widget.setProperty("role", "metric")',
    "primary": 'widget.setProperty("role", "primary")',
    "danger_role": 'widget.setProperty("role", "danger")',
    "status_live": 'widget.setProperty("status", "live")',
    "status_running": 'widget.setProperty("status", "running")',
    "status_completed": 'widget.setProperty("status", "completed")',
    "status_failed": 'widget.setProperty("status", "failed")',
    "status_cancelled": 'widget.setProperty("status", "cancelled")',
}







@dataclass
class QtUsage:
    component: str
    line: int
    column: int
    usage_type: str
    expression: str
    context: str


@dataclass
class WidgetRecord:
    variable_name: str
    component: str
    line: int
    parent_expression: str | None = None

    object_name: str | None = None

    properties: dict[str, str] = field(default_factory=dict)

    methods: list[str] = field(default_factory=list)

    style_lines: list[int] = field(default_factory=list)

    semantic_hints: list[str] = field(default_factory=list)


@dataclass
class StyleFinding:
    line: int
    category: str
    text: str
    selector: str | None = None


@dataclass
class FileReport:
    path: str

    imports: list[str] = field(default_factory=list)

    qt_usages: list[QtUsage] = field(default_factory=list)

    widgets: list[WidgetRecord] = field(default_factory=list)

    style_findings: list[StyleFinding] = field(default_factory=list)

    classes: list[str] = field(default_factory=list)







class QtThemeMigrationScanner:
    """
    Targeted Qt/theme migration scanner.

    It resolves explicitly requested filenames recursively from PROJECT_ROOT
    and produces a detailed source-context report for theme migration.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root

        self.target_files: list[Path] = []

        self.reports: list[FileReport] = []

        self.errors: list[str] = []





    def scan(self) -> None:
        print()
        print("=" * 90)
        print("MOCKAPP QT THEME MIGRATION SCANNER")
        print("=" * 90)
        print()
        print(f"Scanner root: {self.project_root}")
        print()

        self._resolve_targets()

        if not self.target_files:
            print("No target files selected.")
            print()
            return

        print(f"Target files resolved: {len(self.target_files)}")
        print()

        for index, path in enumerate(
            self.target_files,
            start=1,
        ):
            print(f"[{index:>3}/{len(self.target_files)}] " f"{self._relative(path)}")

            self._scan_file(path)

        print()
        print("Scanning complete.")
        print()





    def _resolve_targets(self) -> None:
        """
        Resolve target filenames recursively.

        Example:

            TARGET_FILES = ["browser_window.py"]

        can resolve:

            X:\MOCKAPP\browser_window.py

        or:

            X:\MOCKAPP\some\module\browser_window.py
        """

        if not TARGET_FILES:
            return

        for requested_name in TARGET_FILES:

            requested = Path(requested_name)





            if len(requested.parts) > 1:

                candidate = self.project_root / requested

                if candidate.is_file():
                    self._add_target(candidate)
                    continue





            matches = []

            for path in self.project_root.rglob(requested.name):

                if self._is_excluded(path):
                    continue

                if path.is_file():
                    matches.append(path)

            if not matches:

                self.errors.append(f"Target file not found: " f"{requested_name}")

                continue

            if len(matches) > 1:

                self.errors.append(
                    f"Multiple files matched "
                    f"'{requested_name}': "
                    + ", ".join(self._relative(path) for path in matches)
                )



                continue

            self._add_target(matches[0])

    def _add_target(self, path: Path) -> None:
        if path not in self.target_files:
            self.target_files.append(path)





    def _scan_file(self, path: Path) -> None:

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except Exception as exc:

            self.errors.append(
                f"{self._relative(path)}: " f"Could not read file: {exc}"
            )

            return

        try:
            tree = ast.parse(
                source,
                filename=str(path),
            )

        except SyntaxError as exc:

            self.errors.append(
                f"{self._relative(path)}: "
                f"SyntaxError at line "
                f"{exc.lineno}: {exc.msg}"
            )

            return

        report = FileReport(path=self._relative(path))

        self._scan_imports(
            tree,
            report,
        )

        self._scan_classes(
            tree,
            report,
        )

        self._scan_qt_usage(
            tree,
            source,
            report,
        )

        self._scan_style_findings(
            source,
            report,
        )

        self._attach_style_lines_to_widgets(
            report,
        )

        self._infer_semantic_hints(
            report,
        )

        self.reports.append(report)





    def _scan_imports(
        self,
        tree: ast.AST,
        report: FileReport,
    ) -> None:

        for node in ast.walk(tree):

            if isinstance(node, ast.ImportFrom):

                module = node.module or ""

                if not self._is_qt_module(module):
                    continue

                for alias in node.names:

                    report.imports.append(f"from {module} import {alias.name}")

            elif isinstance(node, ast.Import):

                for alias in node.names:

                    if self._is_qt_module(alias.name):

                        report.imports.append(f"import {alias.name}")





    def _scan_classes(
        self,
        tree: ast.AST,
        report: FileReport,
    ) -> None:

        for node in ast.walk(tree):

            if not isinstance(node, ast.ClassDef):
                continue

            bases = []

            for base in node.bases:

                name = self._expression_name(base)

                if name:
                    bases.append(name)

            if bases:

                report.classes.append(
                    f"{node.name} " f"({', '.join(bases)}) " f"[line {node.lineno}]"
                )

            else:

                report.classes.append(f"{node.name} " f"[line {node.lineno}]")


            for base in bases:

                if base in KNOWN_QT_COMPONENTS:

                    report.qt_usages.append(
                        QtUsage(
                            component=base,
                            line=node.lineno,
                            column=node.col_offset,
                            usage_type="class inheritance",
                            expression=(f"class {node.name}({base})"),
                            context=(
                                "Class derives from a Qt " "visual/component class."
                            ),
                        )
                    )





    def _scan_qt_usage(
        self,
        tree: ast.AST,
        source: str,
        report: FileReport,
    ) -> None:

        source_lines = source.splitlines()





        aliases: dict[str, str] = {}

        for node in ast.walk(tree):

            if isinstance(node, ast.ImportFrom):

                module = node.module or ""

                if not self._is_qt_module(module):
                    continue

                for alias in node.names:

                    aliases[alias.asname or alias.name] = alias.name

            elif isinstance(node, ast.Import):

                for alias in node.names:

                    if self._is_qt_module(alias.name):

                        aliases[alias.asname or alias.name] = alias.name





        for node in ast.walk(tree):









            if isinstance(node, ast.Call):

                expression = self._expression_name(node.func)

                if expression:

                    component = aliases.get(expression) or expression.split(".")[-1]

                    if component in KNOWN_QT_COMPONENTS:

                        context = self._context_for_node(
                            node,
                            source_lines,
                        )

                        usage = QtUsage(
                            component=component,
                            line=node.lineno,
                            column=node.col_offset,
                            usage_type="constructor",
                            expression=expression,
                            context=context,
                        )

                        report.qt_usages.append(usage)

                        variable_name = self._find_assigned_variable(
                            tree,
                            node,
                        )

                        if variable_name:

                            widget = WidgetRecord(
                                variable_name=variable_name,
                                component=component,
                                line=node.lineno,
                                parent_expression=(self._extract_parent_argument(node)),
                            )

                            report.widgets.append(widget)








            elif isinstance(node, ast.Attribute):

                component = node.attr

                if component not in KNOWN_QT_COMPONENTS:
                    continue


                if isinstance(
                    node.parent if hasattr(node, "parent") else None, ast.Call
                ):
                    continue

                context = self._context_for_node(
                    node,
                    source_lines,
                )

                report.qt_usages.append(
                    QtUsage(
                        component=component,
                        line=node.lineno,
                        column=node.col_offset,
                        usage_type="qualified/reference",
                        expression=ast.unparse(node),
                        context=context,
                    )
                )





    def _scan_style_findings(
        self,
        source: str,
        report: FileReport,
    ) -> None:

        lines = source.splitlines()

        current_selector: str | None = None
        in_stylesheet = False
        stylesheet_brace_depth = 0

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            stripped = line.strip()





            if "setStyleSheet" in line:

                in_stylesheet = True

                report.style_findings.append(
                    StyleFinding(
                        line=line_number,
                        category="setStyleSheet",
                        text=line.strip(),
                    )
                )





            if in_stylesheet:

                if "{" in line:

                    stylesheet_brace_depth += line.count("{") - line.count("}")

                    selector_candidate = stripped.split("{", 1)[0].strip()

                    if selector_candidate:
                        current_selector = selector_candidate

                else:

                    stylesheet_brace_depth += line.count("{") - line.count("}")





                for category, pattern in STYLE_PATTERNS.items():

                    if category in {
                        "setStyleSheet",
                        "setPalette",
                    }:
                        continue

                    if pattern.search(line):

                        report.style_findings.append(
                            StyleFinding(
                                line=line_number,
                                category=category,
                                text=line.strip(),
                                selector=current_selector,
                            )
                        )

                if stylesheet_brace_depth <= 0:

                    in_stylesheet = False
                    current_selector = None
                    stylesheet_brace_depth = 0

            else:





                for category, pattern in STYLE_PATTERNS.items():

                    if pattern.search(line):

                        report.style_findings.append(
                            StyleFinding(
                                line=line_number,
                                category=category,
                                text=line.strip(),
                            )
                        )





    def _attach_style_lines_to_widgets(
        self,
        report: FileReport,
    ) -> None:

        for widget in report.widgets:

            for finding in report.style_findings:







                distance = finding.line - widget.line

                if 0 <= distance <= 80:

                    widget.style_lines.append(finding.line)





    def _infer_semantic_hints(
        self,
        report: FileReport,
    ) -> None:

        for widget in report.widgets:

            name = widget.variable_name.lower()
            component = widget.component





            if component in {
                "QMainWindow",
                "QFrame",
                "QGroupBox",
                "QWidget",
            }:

                if any(
                    token in name
                    for token in (
                        "workspace",
                        "panel",
                        "content",
                        "container",
                        "page",
                        "body",
                    )
                ):

                    widget.semantic_hints.append("surface / panel")

                if any(
                    token in name
                    for token in (
                        "sidebar",
                        "side",
                        "left_panel",
                        "right_panel",
                    )
                ):

                    widget.semantic_hints.append("sidebar")

                if any(
                    token in name
                    for token in (
                        "header",
                        "toolbar",
                        "navigation",
                        "nav",
                    )
                ):

                    widget.semantic_hints.append("navigation / header surface")

                if any(
                    token in name
                    for token in (
                        "status",
                        "footer",
                    )
                ):

                    widget.semantic_hints.append("status surface")





            if component == "QLabel":

                if any(
                    token in name
                    for token in (
                        "status",
                        "description",
                        "secondary",
                        "subtitle",
                        "hint",
                        "muted",
                    )
                ):

                    widget.semantic_hints.append("muted text")

                if any(
                    token in name
                    for token in (
                        "title",
                        "heading",
                        "header",
                    )
                ):

                    widget.semantic_hints.append("title text")

                if any(
                    token in name
                    for token in (
                        "error",
                        "failed",
                    )
                ):

                    widget.semantic_hints.append("danger status")

                if any(
                    token in name
                    for token in (
                        "success",
                        "completed",
                        "ready",
                    )
                ):

                    widget.semantic_hints.append("success/completed status")





            if component in {
                "QLineEdit",
                "QTextEdit",
                "QPlainTextEdit",
                "QComboBox",
                "QSpinBox",
                "QDoubleSpinBox",
            }:

                widget.semantic_hints.append("input")





            if component in {
                "QPushButton",
                "QToolButton",
            }:

                widget.semantic_hints.append("interactive control")

                if any(
                    token in name
                    for token in (
                        "delete",
                        "remove",
                        "cancel",
                        "stop",
                        "deny",
                    )
                ):

                    widget.semantic_hints.append("danger action")

                if any(
                    token in name
                    for token in (
                        "submit",
                        "approve",
                        "confirm",
                        "start",
                        "run",
                    )
                ):

                    widget.semantic_hints.append("primary action")





            if component == "QWebEngineView":

                widget.semantic_hints.append("browser/web surface")





            if component in {
                "QTabBar",
                "QTabWidget",
            }:

                widget.semantic_hints.append("navigation / tabs")





            if component in {
                "QListWidget",
                "QListView",
                "QTreeWidget",
                "QTreeView",
                "QTableWidget",
                "QTableView",
            }:

                widget.semantic_hints.append("data surface")





            if component in {
                "QScrollArea",
                "QAbstractScrollArea",
                "QScrollBar",
            }:

                widget.semantic_hints.append("scrolling surface")





    def _is_excluded(
        self,
        path: Path,
    ) -> bool:

        try:
            relative = path.relative_to(self.project_root)
        except ValueError:
            return True

        return any(part in EXCLUDED_DIRECTORIES for part in relative.parts)

    @staticmethod
    def _is_qt_module(
        module: str,
    ) -> bool:

        if not module:
            return False

        return any(module == root or module.startswith(root + ".") for root in QT_ROOTS)

    @staticmethod
    def _expression_name(
        node: ast.AST,
    ) -> str | None:

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):

            parent = QtThemeMigrationScanner._expression_name(node.value)

            if parent:
                return f"{parent}.{node.attr}"

            return node.attr

        return None

    @staticmethod
    def _find_assigned_variable(
        tree: ast.AST,
        target_call: ast.Call,
    ) -> str | None:

        for node in ast.walk(tree):

            if not isinstance(
                node,
                ast.Assign,
            ):
                continue

            if node.value is not target_call:
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if isinstance(
                target,
                ast.Name,
            ):

                return target.id

        return None

    @staticmethod
    def _extract_parent_argument(
        node: ast.Call,
    ) -> str | None:

        for keyword in node.keywords:

            if keyword.arg == "parent":

                try:
                    return ast.unparse(keyword.value)
                except Exception:
                    return None

        return None

    @staticmethod
    def _context_for_node(
        node: ast.AST,
        source_lines: list[str],
        radius: int = 2,
    ) -> str:

        line_number = getattr(
            node,
            "lineno",
            1,
        )

        start = max(
            0,
            line_number - radius - 1,
        )

        end = min(
            len(source_lines),
            line_number + radius,
        )

        output = []

        for index in range(start, end):

            marker = ">>" if index == line_number - 1 else "  "

            output.append(f"{marker} " f"{index + 1:>5}: " f"{source_lines[index]}")

        return "\n".join(output)

    def _relative(
        self,
        path: Path,
    ) -> str:

        return str(path.relative_to(self.project_root)).replace(
            "\\",
            "/",
        )







class MigrationReportWriter:
    """
    Writes a deterministic migration-oriented text report.

    The report is intentionally source-oriented so that it can be used later
    to construct exact find/replace blocks.
    """

    def __init__(
        self,
        scanner: QtThemeMigrationScanner,
        output_file: Path,
    ):
        self.scanner = scanner
        self.output_file = output_file

    def write(self) -> None:

        lines: list[str] = []

        self._header(lines)
        self._summary(lines)
        self._files(lines)
        self._errors(lines)
        self._footer(lines)

        self.output_file.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )





    def _header(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "=" * 90,
                "MOCKAPP QT THEME MIGRATION REPORT",
                "=" * 90,
                "",
                f"Project root: {self.scanner.project_root}",
                "",
                "Purpose:",
                "  Analyze selected MOCKAPP Qt source files before migrating",
                "  local styling to the global qt_theme package.",
                "",
                "The report records:",
                "  - Qt imports",
                "  - Qt component construction",
                "  - Qt inheritance",
                "  - widget variable names",
                "  - object names",
                "  - dynamic properties",
                "  - theme-relevant method calls",
                "  - local stylesheets",
                "  - hard-coded colors",
                "  - typography",
                "  - dimensions",
                "  - semantic theme hints",
                "  - nearby source context",
                "",
                "=" * 90,
                "",
            ]
        )





    def _summary(
        self,
        lines: list[str],
    ) -> None:

        total_qt_usages = sum(len(report.qt_usages) for report in self.scanner.reports)

        total_widgets = sum(len(report.widgets) for report in self.scanner.reports)

        total_style_findings = sum(
            len(report.style_findings) for report in self.scanner.reports
        )

        lines.extend(
            [
                "1. SUMMARY",
                "-" * 90,
                "",
                f"Requested targets: {len(TARGET_FILES)}",
                f"Resolved files: {len(self.scanner.reports)}",
                f"Qt usages detected: {total_qt_usages}",
                f"Widget instances detected: {total_widgets}",
                f"Theme/style findings: {total_style_findings}",
                f"Scanner errors: {len(self.scanner.errors)}",
                "",
            ]
        )





    def _files(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2. SOURCE FILE ANALYSIS",
                "-" * 90,
                "",
            ]
        )

        for report in self.scanner.reports:

            lines.extend(
                [
                    "",
                    "#" * 90,
                    f"FILE: {report.path}",
                    "#" * 90,
                    "",
                ]
            )

            self._imports(
                report,
                lines,
            )

            self._classes(
                report,
                lines,
            )

            self._widgets(
                report,
                lines,
            )

            self._qt_usages(
                report,
                lines,
            )

            self._style_findings(
                report,
                lines,
            )

            self._theme_mapping(
                report,
                lines,
            )





    def _imports(
        self,
        report: FileReport,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2.1 QT IMPORTS",
                "-" * 60,
            ]
        )

        if not report.imports:

            lines.append("  <none>")

        else:

            for item in sorted(set(report.imports)):

                lines.append(f"  {item}")

        lines.append("")





    def _classes(
        self,
        report: FileReport,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2.2 CLASSES / QT INHERITANCE",
                "-" * 60,
            ]
        )

        if not report.classes:

            lines.append("  <none>")

        else:

            for item in report.classes:

                lines.append(f"  {item}")

        lines.append("")





    def _widgets(
        self,
        report: FileReport,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2.3 WIDGET / COMPONENT RECORDS",
                "-" * 60,
                "",
            ]
        )

        if not report.widgets:

            lines.append("  <none detected>")

            lines.append("")

            return

        for index, widget in enumerate(
            report.widgets,
            start=1,
        ):

            lines.extend(
                [
                    f"[WIDGET {index}]",
                    f"  Variable: {widget.variable_name}",
                    f"  Component: {widget.component}",
                    f"  Created at line: {widget.line}",
                ]
            )

            if widget.parent_expression:

                lines.append(f"  Parent: {widget.parent_expression}")

            if widget.object_name:

                lines.append(f"  Object name: {widget.object_name}")

            if widget.properties:

                lines.append("  Properties:")

                for key, value in sorted(widget.properties.items()):

                    lines.append(f"    {key} = {value}")

            if widget.methods:

                lines.append("  Theme-relevant methods:")

                for method in widget.methods:

                    lines.append(f"    {method}")

            if widget.style_lines:

                lines.append("  Nearby style lines:")

                for line in sorted(set(widget.style_lines)):

                    lines.append(f"    line {line}")

            if widget.semantic_hints:

                lines.append("  Semantic hints:")

                for hint in widget.semantic_hints:

                    lines.append(f"    {hint}")

            lines.append("")





    def _qt_usages(
        self,
        report: FileReport,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2.4 QT USAGE WITH SOURCE CONTEXT",
                "-" * 60,
                "",
            ]
        )

        for index, usage in enumerate(
            report.qt_usages,
            start=1,
        ):

            lines.extend(
                [
                    f"[QT USAGE {index}]",
                    f"  Component: {usage.component}",
                    f"  Type: {usage.usage_type}",
                    f"  Line: {usage.line}",
                    f"  Column: {usage.column}",
                    f"  Expression: {usage.expression}",
                    "",
                    "  Context:",
                ]
            )

            for context_line in usage.context.splitlines():

                lines.append(f"    {context_line}")

            lines.append("")





    def _style_findings(
        self,
        report: FileReport,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2.5 LOCAL STYLE / THEME FINDINGS",
                "-" * 60,
                "",
            ]
        )

        if not report.style_findings:

            lines.append("  <none detected>")

            lines.append("")

            return

        for finding in report.style_findings:

            selector_text = ""

            if finding.selector:

                selector_text = f" | selector: {finding.selector}"

            lines.append(
                f"  line {finding.line} | " f"{finding.category}" f"{selector_text}"
            )

            lines.append(f"      {finding.text}")

        lines.append("")





    def _theme_mapping(
        self,
        report: FileReport,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2.6 POTENTIAL GLOBAL THEME MAPPING",
                "-" * 60,
                "",
            ]
        )

        if not report.widgets:

            lines.append("  No widget records available.")

            lines.append("")

            return

        for widget in report.widgets:

            lines.append(f"  {widget.variable_name} " f"({widget.component})")

            if not widget.semantic_hints:

                lines.append("    Theme role: " "<manual review required>")

            else:

                for hint in widget.semantic_hints:

                    mapping = self._mapping_for_hint(hint)

                    lines.append(f"    {hint} -> {mapping}")

            lines.append("")

    @staticmethod
    def _mapping_for_hint(
        hint: str,
    ) -> str:

        mapping = {
            "surface / panel": ('setProperty("role", "panel")'),
            "sidebar": ('setProperty("role", "sidebar")'),
            "navigation / header surface": ("global QSS / surface_alt + border"),
            "status surface": ("global QSS / surface_alt + muted text"),
            "muted text": ('setProperty("role", "muted")'),
            "title text": ('setProperty("role", "title")'),
            "danger status": ('setProperty("status", "failed") ' "or role=danger"),
            "success/completed status": ('setProperty("status", "completed")'),
            "input": ("global QLineEdit/QTextEdit/QComboBox styling"),
            "interactive control": ("global QPushButton/QToolButton styling"),
            "danger action": ('setProperty("role", "danger")'),
            "primary action": ('setProperty("role", "primary")'),
            "browser/web surface": ("global QWebEngineView host styling"),
            "navigation / tabs": ("global QTabBar/QTabWidget styling"),
            "data surface": ("global list/tree/table styling"),
            "scrolling surface": ("global scrollbar/scroll-area styling"),
        }

        return mapping.get(
            hint,
            "<manual review required>",
        )





    def _errors(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "",
                "3. SCANNER ERRORS",
                "-" * 90,
                "",
            ]
        )

        if not self.scanner.errors:

            lines.append("  None.")

            return

        for error in self.scanner.errors:

            lines.append(f"  {error}")





    def _footer(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "",
                "=" * 90,
                "END OF REPORT",
                "=" * 90,
                "",
                "IMPORTANT:",
                "  This report does not modify any MOCKAPP source file.",
                "  It is an analysis artifact for deterministic theme migration.",
                "",
            ]
        )







def main() -> int:

    print("Starting MOCKAPP Qt theme migration scan...")

    if not TARGET_FILES:

        print()
        print("TARGET_FILES is empty.")
        print("Add one or more filenames to TARGET_FILES and run again.")
        print()


        scanner = QtThemeMigrationScanner(PROJECT_ROOT)

        writer = MigrationReportWriter(
            scanner,
            OUTPUT_FILE,
        )

        writer.write()

        print(f"Empty report written to:")

        print(f"  {OUTPUT_FILE}")

        return 0

    try:

        scanner = QtThemeMigrationScanner(PROJECT_ROOT)

        scanner.scan()

        writer = MigrationReportWriter(scanner, OUTPUT_FILE)

        writer.write()

        print("=" * 90)

        print("REPORT GENERATED")

        print(f"  {OUTPUT_FILE}")

        print("=" * 90)

        print()

        return 0

    except Exception as exc:

        print()
        print("FATAL ERROR:")
        print(f"  {type(exc).__name__}: {exc}")
        print()

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
