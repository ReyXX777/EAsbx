from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path





PROJECT_ROOT = Path(r"X:\MOCKAPP")

OUTPUT_FILE = PROJECT_ROOT / "MOCKAPP_QT_COMPONENT_INVENTORY.txt"

PYTHON_EXTENSIONS = {".py"}

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





COMPONENT_GROUPS = {
    "WINDOWS / ROOT CONTAINERS": {
        "QWidget",
        "QMainWindow",
        "QDialog",
        "QDialogButtonBox",
        "QDockWidget",
        "QMdiArea",
        "QMdiSubWindow",
        "QScrollArea",
        "QStackedWidget",
        "QTabWidget",
        "QToolBox",
        "QFrame",
        "QGroupBox",
    },
    "LAYOUTS": {
        "QLayout",
        "QBoxLayout",
        "QVBoxLayout",
        "QHBoxLayout",
        "QGridLayout",
        "QFormLayout",
        "QStackedLayout",
        "QSplitter",
    },
    "TEXT / DISPLAY": {
        "QLabel",
        "QTextBrowser",
        "QTextEdit",
        "QPlainTextEdit",
        "QLCDNumber",
        "QProgressBar",
        "QCalendarWidget",
    },
    "BUTTONS / ACTIONS": {
        "QPushButton",
        "QToolButton",
        "QRadioButton",
        "QCheckBox",
        "QCommandLinkButton",
        "QAbstractButton",
        "QAction",
        "QActionGroup",
    },
    "INPUT CONTROLS": {
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
    },
    "LIST / TREE / TABLE": {
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
    },
    "NAVIGATION": {
        "QTabBar",
        "QTabWidget",
        "QToolBar",
        "QMenuBar",
        "QMenu",
        "QStatusBar",
    },
    "DIALOGS / POPUPS": {
        "QMessageBox",
        "QFileDialog",
        "QColorDialog",
        "QFontDialog",
        "QInputDialog",
        "QProgressDialog",
        "QErrorMessage",
    },
    "SCROLLING": {
        "QScrollBar",
        "QAbstractScrollArea",
        "QScrollArea",
    },
    "GRAPHICS / PAINTING": {
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
    },
    "MODEL / VIEW / CORE": {
        "QObject",
        "QModelIndex",
        "QAbstractItemModel",
        "QAbstractListModel",
        "QAbstractTableModel",
        "QStandardItemModel",
        "QStandardItem",
        "QItemSelectionModel",
        "QSortFilterProxyModel",
    },
    "WEB / BROWSER": {
        "QWebEngineView",
        "QWebEnginePage",
        "QWebEngineProfile",
        "QWebEngineSettings",
        "QWebEngineDownloadRequest",
        "QWebEngineFullScreenRequest",
        "QWebChannel",
    },
    "APPLICATION / EVENT LOOP": {
        "QApplication",
        "QGuiApplication",
        "QCoreApplication",
        "QEvent",
        "QTimer",
        "QThread",
        "QThreadPool",
        "QRunnable",
    },
    "WINDOW / SCREEN / SYSTEM": {
        "QScreen",
        "QWindow",
        "QSystemTrayIcon",
        "QClipboard",
    },
    "OTHER QT COMPONENTS": set(),
}






THEME_PATTERNS = {
    "setStyleSheet()": re.compile(
        r"\.setStyleSheet\s*\(",
        re.IGNORECASE,
    ),
    "setPalette()": re.compile(
        r"\.setPalette\s*\(",
        re.IGNORECASE,
    ),
    "QPalette": re.compile(
        r"\bQPalette\b",
    ),
    "QColor": re.compile(
        r"\bQColor\b",
    ),
    "hex color": re.compile(
        r"#[0-9a-fA-F]{3,8}\b",
    ),
    "rgb()/rgba()": re.compile(
        r"\brgba?\s*\(",
        re.IGNORECASE,
    ),
    "named color": re.compile(
        r"""
        (?:
            color
            |
            background
            |
            foreground
        )
        \s*[:=]
        \s*
        ["']
        (?:
            black|
            white|
            red|
            green|
            blue|
            gray|
            grey|
            transparent
        )
        ["']
        """,
        re.IGNORECASE | re.VERBOSE,
    ),
}







@dataclass
class ComponentUsage:
    name: str
    modules: set[str] = field(default_factory=set)
    files: set[str] = field(default_factory=set)
    lines: set[int] = field(default_factory=set)


@dataclass
class FileReport:
    path: str

    imports: list[str] = field(default_factory=list)

    components: dict[str, set[int]] = field(default_factory=lambda: defaultdict(set))

    theme_risks: dict[str, set[int]] = field(default_factory=lambda: defaultdict(set))

    qt_modules: set[str] = field(default_factory=set)







class QtComponentScanner:
    """AST-based Qt component and theme-risk scanner."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

        self.component_usage: dict[str, ComponentUsage] = {}

        self.file_reports: list[FileReport] = []

        self.qt_modules: dict[str, set[str]] = defaultdict(set)

        self.theme_risks: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

        self.errors: list[str] = []





    def scan(self) -> None:
        print()
        print("=" * 78)
        print("MOCKAPP Qt COMPONENT SCANNER")
        print("=" * 78)
        print()
        print(f"Project: {self.project_root}")
        print()

        if not self.project_root.exists():
            raise FileNotFoundError(f"Project root does not exist: {self.project_root}")

        files = list(self._python_files())

        print(f"Python files discovered: {len(files)}")
        print()

        for index, path in enumerate(files, start=1):
            print(f"[{index:>4}/{len(files)}] " f"{self._relative(path)}")

            self._scan_file(path)

        print()
        print("Scan complete.")
        print()





    def _python_files(self):
        for path in self.project_root.rglob("*.py"):
            if self._is_excluded(path):
                continue

            yield path

    def _is_excluded(self, path: Path) -> bool:
        try:
            relative = path.relative_to(self.project_root)
        except ValueError:
            return True

        return any(part in EXCLUDED_DIRECTORIES for part in relative.parts)





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
                f"SyntaxError at line {exc.lineno}: {exc.msg}"
            )
            return

        report = FileReport(
            path=self._relative(path),
        )

        self._scan_imports(
            tree,
            report,
        )

        self._scan_ast_usage(
            tree,
            report,
        )

        self._scan_theme_patterns(
            source,
            report,
        )

        self.file_reports.append(
            report,
        )





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

                report.qt_modules.add(module)

                for alias in node.names:

                    imported_name = alias.name

                    report.imports.append(f"from {module} import {imported_name}")

                    self._register_component(
                        name=imported_name,
                        module=module,
                        file=report.path,
                        line=node.lineno,
                    )





            elif isinstance(node, ast.Import):

                for alias in node.names:

                    if not self._is_qt_module(alias.name):
                        continue

                    report.qt_modules.add(alias.name)

                    report.imports.append(f"import {alias.name}")





    def _scan_ast_usage(
        self,
        tree: ast.AST,
        report: FileReport,
    ) -> None:

        for node in ast.walk(tree):





            if isinstance(node, ast.Call):

                function_name = self._call_name(
                    node.func,
                )

                if function_name:
                    component = self._known_component(
                        function_name,
                    )

                    if component:
                        report.components[component].add(node.lineno)

                        self._register_component(
                            name=component,
                            module="usage",
                            file=report.path,
                            line=node.lineno,
                        )





            if isinstance(node, ast.Attribute):

                attribute = node.attr

                component = self._known_component(
                    attribute,
                )

                if component:

                    report.components[component].add(node.lineno)

                    self._register_component(
                        name=component,
                        module="qualified usage",
                        file=report.path,
                        line=node.lineno,
                    )





    def _scan_theme_patterns(
        self,
        source: str,
        report: FileReport,
    ) -> None:

        lines = source.splitlines()

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            for risk_name, pattern in THEME_PATTERNS.items():

                if pattern.search(line):

                    report.theme_risks[risk_name].add(line_number)

                    self.theme_risks[risk_name][report.path].add(line_number)





    @staticmethod
    def _is_qt_module(
        module: str,
    ) -> bool:

        if not module:
            return False

        return any(module == root or module.startswith(root + ".") for root in QT_ROOTS)

    @staticmethod
    def _call_name(
        node: ast.AST,
    ) -> str | None:

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            return node.attr

        return None

    @staticmethod
    def _known_component(
        name: str,
    ) -> str | None:

        for components in COMPONENT_GROUPS.values():

            if name in components:
                return name

        return None

    def _register_component(
        self,
        name: str,
        module: str,
        file: str,
        line: int,
    ) -> None:

        usage = self.component_usage.get(
            name,
        )

        if usage is None:

            usage = ComponentUsage(
                name=name,
            )

            self.component_usage[name] = usage

        usage.modules.add(
            module,
        )

        usage.files.add(
            file,
        )

        usage.lines.add(
            line,
        )

    def _relative(
        self,
        path: Path,
    ) -> str:

        return str(
            path.relative_to(
                self.project_root,
            )
        ).replace(
            "\\",
            "/",
        )







class InventoryWriter:
    """Writes the complete Qt/theme inventory."""

    def __init__(
        self,
        scanner: QtComponentScanner,
        output_file: Path,
    ) -> None:

        self.scanner = scanner
        self.output_file = output_file

    def write(self) -> None:

        lines: list[str] = []

        self._header(
            lines,
        )

        self._summary(
            lines,
        )

        self._components_by_group(
            lines,
        )

        self._unclassified_components(
            lines,
        )

        self._qt_modules(
            lines,
        )

        self._theme_risks(
            lines,
        )

        self._file_usage(
            lines,
        )

        self._errors(
            lines,
        )

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
                "=" * 78,
                "MOCKAPP QT COMPONENT INVENTORY",
                "=" * 78,
                "",
                f"Project root:",
                f"  {self.scanner.project_root}",
                "",
                "Purpose:",
                "  Inventory all Qt/PySide/PyQt components used by MOCKAPP.",
                "  The report is intended to serve as the source inventory",
                "  for the standalone global Qt theme package.",
                "",
                "=" * 78,
                "",
            ]
        )





    def _summary(
        self,
        lines: list[str],
    ) -> None:

        files = self.scanner.file_reports

        qt_files = [
            report
            for report in files
            if report.qt_modules or report.components or report.theme_risks
        ]

        lines.extend(
            [
                "1. SUMMARY",
                "-" * 78,
                "",
                f"Python files scanned: {len(files)}",
                f"Files containing Qt usage: {len(qt_files)}",
                (
                    "Unique Qt components detected: "
                    f"{len(self.scanner.component_usage)}"
                ),
                ("Theme-risk categories detected: " f"{len(self.scanner.theme_risks)}"),
                ("Scanner errors: " f"{len(self.scanner.errors)}"),
                "",
            ]
        )





    def _components_by_group(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "2. QT COMPONENTS BY GROUP",
                "-" * 78,
                "",
            ]
        )

        for group_name, known_components in COMPONENT_GROUPS.items():

            lines.extend(
                [
                    "",
                    group_name,
                    "~" * len(group_name),
                ]
            )

            found = []

            for name in known_components:

                if name in self.scanner.component_usage:

                    found.append(
                        name,
                    )

            for name in sorted(found):

                usage = self.scanner.component_usage[name]

                lines.append(
                    f"{name} "
                    f"({len(usage.files)} file"
                    f"{'s' if len(usage.files) != 1 else ''})"
                )

                for file in sorted(
                    usage.files,
                ):

                    line_numbers = []

                    report = next(
                        (r for r in self.scanner.file_reports if r.path == file),
                        None,
                    )

                    if report is not None:

                        line_numbers = sorted(
                            report.components.get(
                                name,
                                set(),
                            )
                        )

                    if line_numbers:

                        line_text = ", ".join(str(number) for number in line_numbers)

                        lines.append(f"    {file} " f"[lines: {line_text}]")

                    else:

                        lines.append(f"    {file}")

            if not found:

                lines.append("  <none detected>")

            lines.append("")





    def _unclassified_components(
        self,
        lines: list[str],
    ) -> None:

        known = set()

        for components in COMPONENT_GROUPS.values():
            known.update(
                components,
            )

        unknown = sorted(
            name for name in self.scanner.component_usage if name not in known
        )

        lines.extend(
            [
                "",
                "3. OTHER / UNCLASSIFIED QT COMPONENTS",
                "-" * 78,
                "",
            ]
        )

        if not unknown:

            lines.append("  <none detected>")

            return

        for name in unknown:

            usage = self.scanner.component_usage[name]

            lines.append(f"{name}")

            for file in sorted(
                usage.files,
            ):

                lines.append(f"    {file}")





    def _qt_modules(
        self,
        lines: list[str],
    ) -> None:

        module_usage: dict[str, set[str]] = defaultdict(set)

        for report in self.scanner.file_reports:

            for module in report.qt_modules:

                module_usage[module].add(report.path)

        lines.extend(
            [
                "",
                "4. QT MODULES",
                "-" * 78,
                "",
            ]
        )

        if not module_usage:

            lines.append("  <none detected>")

            return

        for module in sorted(
            module_usage,
        ):

            lines.append(module)

            for file in sorted(
                module_usage[module],
            ):

                lines.append(f"    {file}")





    def _theme_risks(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "",
                "5. THEME / STYLE RISK ANALYSIS",
                "-" * 78,
                "",
                (
                    "These findings identify existing code that may "
                    "override or conflict with the global theme."
                ),
                "",
            ]
        )

        if not self.scanner.theme_risks:

            lines.append("  No explicit theme-risk patterns detected.")

            return

        for risk_name in sorted(
            self.scanner.theme_risks,
        ):

            lines.extend(
                [
                    "",
                    risk_name,
                    "~" * len(risk_name),
                ]
            )

            file_map = self.scanner.theme_risks[risk_name]

            for file in sorted(
                file_map,
            ):

                line_numbers = sorted(file_map[file])

                line_text = ", ".join(str(number) for number in line_numbers)

                lines.append(f"    {file} " f"[lines: {line_text}]")





    def _file_usage(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "",
                "6. QT USAGE BY SOURCE FILE",
                "-" * 78,
                "",
            ]
        )

        for report in sorted(
            self.scanner.file_reports,
            key=lambda item: item.path.lower(),
        ):

            if not (report.qt_modules or report.components or report.theme_risks):
                continue

            lines.extend(
                [
                    "",
                    report.path,
                    "~" * len(report.path),
                ]
            )

            if report.qt_modules:

                lines.append("Qt modules:")

                for module in sorted(
                    report.qt_modules,
                ):

                    lines.append(f"    {module}")

            if report.components:

                lines.append("Components:")

                for component in sorted(
                    report.components,
                ):

                    line_numbers = sorted(report.components[component])

                    lines.append(
                        f"    {component} "
                        f"[lines: "
                        f"{', '.join(map(str, line_numbers))}]"
                    )

            if report.theme_risks:

                lines.append("Theme risks:")

                for risk in sorted(
                    report.theme_risks,
                ):

                    line_numbers = sorted(report.theme_risks[risk])

                    lines.append(
                        f"    {risk} "
                        f"[lines: "
                        f"{', '.join(map(str, line_numbers))}]"
                    )





    def _errors(
        self,
        lines: list[str],
    ) -> None:

        lines.extend(
            [
                "",
                "7. SCANNER ERRORS",
                "-" * 78,
                "",
            ]
        )

        if not self.scanner.errors:

            lines.append("  None.")

            return

        for error in self.scanner.errors:

            lines.append(f"  {error}")







def print_console_summary(
    scanner: QtComponentScanner,
) -> None:

    print()
    print("=" * 78)
    print("SCAN SUMMARY")
    print("=" * 78)

    print(f"Qt components: " f"{len(scanner.component_usage)}")

    print(
        f"Qt-related files: "
        f"{sum(bool(r.qt_modules or r.components) for r in scanner.file_reports)}"
    )

    print(f"Theme-risk categories: " f"{len(scanner.theme_risks)}")

    print(f"Errors: " f"{len(scanner.errors)}")

    print()

    print("Detected components:")

    for name in sorted(
        scanner.component_usage,
    ):

        usage = scanner.component_usage[name]

        print(f"  {name:<32} " f"{len(usage.files)} file(s)")

    print()
    print("=" * 78)
    print()







def main() -> int:

    print("Starting MOCKAPP Qt component inventory...")

    try:

        scanner = QtComponentScanner(
            PROJECT_ROOT,
        )

        scanner.scan()

        writer = InventoryWriter(
            scanner,
            OUTPUT_FILE,
        )

        writer.write()

        print_console_summary(
            scanner,
        )

        print(f"Inventory written to:")

        print(f"  {OUTPUT_FILE}")

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
