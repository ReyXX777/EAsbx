from __future__ import annotations

"""
Deterministic Qt UI object inventory extractor.

Purpose
-------
Statically inspect a PySide6/PyQt-style Python source file and extract:

    - Qt widget classes
    - objectName values
    - constructor arguments where useful
    - parent/container relationships
    - likely semantic roles
    - state/property information
    - suggested Qt stylesheet selectors

The generated JSON is intended to be an architectural intermediate
representation for extending qt_theme/stylesheet.py.

IMPORTANT
---------
This script does NOT modify the source file or stylesheet.py.

It deliberately uses AST analysis rather than executing the application.
Therefore:

    - no QApplication is created
    - no Gemini API is called
    - no widgets are instantiated
    - no application code is executed

This makes the result deterministic and safe to run during refactoring.

Usage
-----
From X:\\MOCKAPP:

    python qt_theme/extract_ui_objects.py chat_window.py

Optional output path:

    python qt_theme/extract_ui_objects.py chat_window.py \
        --output qt_theme/chat_window_objects.json

If no input file is supplied, the script defaults to:

    chat_window.py
"""

import argparse
import ast
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional





QT_WIDGET_CLASSES = {

    "QWidget",
    "QFrame",
    "QLabel",
    "QLineEdit",
    "QTextEdit",
    "QPlainTextEdit",
    "QPushButton",
    "QToolButton",
    "QComboBox",
    "QCheckBox",
    "QRadioButton",
    "QListWidget",
    "QTreeWidget",
    "QTableWidget",
    "QTableView",
    "QSpinBox",
    "QDoubleSpinBox",
    "QDateEdit",
    "QTimeEdit",
    "QDateTimeEdit",

    "QGroupBox",
    "QTabWidget",
    "QStackedWidget",
    "QScrollArea",
    "QSplitter",

    "QMainWindow",
    "QDialog",
    "QStatusBar",
    "QMenuBar",

    "QWebEngineView",

    "QProgressBar",
    "QSlider",
    "QDial",
    "QToolBar",
    "QCalendarWidget",
}






"""
The semantic role system is intentionally conservative.

The extractor should NOT invent dozens of roles.

The first goal is to identify reusable categories such as:

    panel
    header
    title
    subtitle
    status
    input
    primary_action
    secondary_action
    icon_button
    selector
    conversation_display
    composer
    hint
    approval_container
    indicator

These roles can later become stable stylesheet APIs.
"""


ROLE_RULES = (



    ("chatWindow", "chat_root"),
    ("chatHeader", "header"),
    ("chatDisplay", "conversation_display"),
    ("approvalContainer", "approval_container"),
    ("composerOuter", "composer"),
    ("inputCard", "input_card"),
    ("agentIcon", "agent_icon"),
    ("agentTitle", "title"),
    ("agentStatus", "status"),
    ("statusIndicator", "status_indicator"),
    ("headerButton", "secondary_action"),
    ("composerIconButton", "icon_button"),
    ("messageInput", "text_input"),
    ("modeDropdown", "selector"),
    ("sendButton", "primary_action"),
    ("composerHint", "hint"),
    ("composerShortcut", "shortcut"),



    ("title", "title"),
    ("subtitle", "subtitle"),
    ("status", "status"),
    ("indicator", "status_indicator"),
    ("header", "header"),
    ("sidebar", "sidebar"),
    ("panel", "panel"),
    ("input", "text_input"),
    ("editor", "editor"),
    ("display", "display"),
    ("dropdown", "selector"),
    ("combo", "selector"),
    ("selector", "selector"),
    ("send", "primary_action"),
    ("submit", "primary_action"),
    ("primary", "primary_action"),
    ("iconbutton", "icon_button"),
    ("icon_button", "icon_button"),
    ("button", "secondary_action"),
    ("hint", "hint"),
    ("shortcut", "shortcut"),
    ("approval", "approval"),
    ("composer", "composer"),
    ("list", "list"),
    ("table", "table"),
    ("tree", "tree"),
    ("scroll", "scroll_area"),
)







@dataclass
class ObjectRecord:
    class_name: str
    variable_name: str
    object_name: Optional[str]
    semantic_role: str
    confidence: str

    source_line: int

    parent_variable: Optional[str] = None

    constructor_text: Optional[str] = None

    properties: dict = field(default_factory=dict)

    suggested_selectors: list[str] = field(default_factory=list)

    notes: list[str] = field(default_factory=list)







def dotted_name(node: ast.AST) -> Optional[str]:
    """
    Return a dotted Python name from an AST node.

    Examples:

        QLabel       -> "QLabel"
        QtWidgets.QLabel -> "QtWidgets.QLabel"

    Returns None when the node cannot be represented as a name.
    """

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return None


def literal_value(node: Optional[ast.AST]):
    """
    Safely extract simple Python literals from the AST.

    We intentionally do not evaluate arbitrary expressions.
    """

    if node is None:
        return None

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, (ast.List, ast.Tuple)):
        values = []

        for element in node.elts:
            values.append(literal_value(element))

        return values

    if isinstance(node, ast.Dict):
        result = {}

        for key, value in zip(node.keys, node.values):
            key_value = literal_value(key)

            if key_value is not None:
                result[str(key_value)] = literal_value(value)

        return result

    return None


def source_segment(source: str, node: ast.AST) -> Optional[str]:
    """
    Return source text for an AST node when available.
    """

    try:
        return ast.get_source_segment(source, node)
    except Exception:
        return None


def assignment_target_name(node: ast.AST) -> Optional[str]:
    """
    Extract a simple assignment target.

        self.chat_display = ...
        self.chat_display

    returns:

        chat_display
    """

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return node.attr

    return None


def is_self_attribute(node: ast.AST) -> bool:
    """
    Return True for:

        self.foo
    """

    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )







class UIObjectExtractor(ast.NodeVisitor):
    """
    AST visitor that builds a deterministic widget inventory.
    """

    def __init__(self, source: str):
        self.source = source

        self.objects: list[ObjectRecord] = []

        self.current_function: Optional[str] = None


        self.widget_variables: dict[str, str] = {}


        self.object_names: dict[str, str] = {}


        self.parent_variables: dict[str, str] = {}


        self.properties: dict[str, dict] = {}





    def visit_FunctionDef(self, node: ast.FunctionDef):
        previous = self.current_function

        self.current_function = node.name

        self.generic_visit(node)

        self.current_function = previous

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        previous = self.current_function

        self.current_function = node.name

        self.generic_visit(node)

        self.current_function = previous





    def visit_Assign(self, node: ast.Assign):
        """
        Detect:

            self.chat_display = QTextEdit()

        and:

            self.chat_display.setObjectName(...)

        indirectly through variable tracking.
        """

        value = node.value

        widget_class = self._widget_class_from_constructor(value)

        if widget_class:
            constructor_text = source_segment(self.source, value)

            for target in node.targets:
                variable_name = assignment_target_name(target)

                if not variable_name:
                    continue

                self.widget_variables[variable_name] = widget_class

                parent_variable = self._parent_from_constructor(value)

                if parent_variable:
                    self.parent_variables[variable_name] = parent_variable

                self.properties.setdefault(variable_name, {})

                self.objects.append(
                    ObjectRecord(
                        class_name=widget_class,
                        variable_name=variable_name,
                        object_name=None,
                        semantic_role="unclassified",
                        confidence="unknown",
                        source_line=node.lineno,
                        parent_variable=parent_variable,
                        constructor_text=constructor_text,
                    )
                )

        self.generic_visit(node)





    def visit_Call(self, node: ast.Call):
        """
        Detect important widget property calls.

        Currently:

            setObjectName(...)
            setText(...)
            setPlaceholderText(...)
            setToolTip(...)
            setFixedSize(...)
            setFixedHeight(...)
            setMinimumWidth(...)
            setReadOnly(...)
            setEnabled(...)
            setVisible(...)
        """

        if isinstance(node.func, ast.Attribute):
            method = node.func.attr

            if is_self_attribute(node.func.value):
                variable_name = node.func.value.attr

                self._record_method(
                    variable_name,
                    method,
                    node,
                )

        self.generic_visit(node)





    def _widget_class_from_constructor(
        self,
        node: ast.AST,
    ) -> Optional[str]:

        if not isinstance(node, ast.Call):
            return None

        name = dotted_name(node.func)

        if not name:
            return None

        class_name = name.split(".")[-1]

        if class_name in QT_WIDGET_CLASSES:
            return class_name

        return None

    def _parent_from_constructor(
        self,
        node: ast.AST,
    ) -> Optional[str]:

        if not isinstance(node, ast.Call):
            return None












        for keyword in node.keywords:
            if keyword.arg != "parent":
                continue

            value = keyword.value

            if is_self_attribute(value):
                return value.attr

            if isinstance(value, ast.Name):
                return value.id


        if node.args:
            candidate = node.args[-1]

            if is_self_attribute(candidate):
                return candidate.attr

            if isinstance(candidate, ast.Name):
                return candidate.id

        return None





    def _record_method(
        self,
        variable_name: str,
        method: str,
        node: ast.Call,
    ):
        if variable_name not in self.widget_variables:
            return

        properties = self.properties.setdefault(
            variable_name,
            {},
        )

        value = None

        if node.args:
            value = literal_value(node.args[0])

        if method == "setObjectName":
            if isinstance(value, str):
                self.object_names[variable_name] = value

        elif method == "setText":
            if isinstance(value, str):
                properties["text"] = value

        elif method == "setPlaceholderText":
            if isinstance(value, str):
                properties["placeholder_text"] = value

        elif method == "setToolTip":
            if isinstance(value, str):
                properties["tooltip"] = value

        elif method == "setFixedHeight":
            if isinstance(value, (int, float)):
                properties["fixed_height"] = value

        elif method == "setFixedWidth":
            if isinstance(value, (int, float)):
                properties["fixed_width"] = value

        elif method == "setMinimumWidth":
            if isinstance(value, (int, float)):
                properties["minimum_width"] = value

        elif method == "setMinimumHeight":
            if isinstance(value, (int, float)):
                properties["minimum_height"] = value

        elif method == "setFixedSize":
            values = [literal_value(argument) for argument in node.args]

            if all(value is not None for value in values):
                properties["fixed_size"] = values

        elif method == "setReadOnly":
            if isinstance(value, bool):
                properties["read_only"] = value

        elif method == "setEnabled":
            if isinstance(value, bool):
                properties["enabled"] = value

        elif method == "setVisible":
            if isinstance(value, bool):
                properties["visible"] = value

        elif method == "setAcceptRichText":
            if isinstance(value, bool):
                properties["accept_rich_text"] = value





    def finalize(self) -> list[ObjectRecord]:
        """
        Resolve object names, semantic roles, selectors and properties.
        """

        for record in self.objects:
            variable_name = record.variable_name

            record.object_name = self.object_names.get(variable_name)

            record.properties.update(
                self.properties.get(
                    variable_name,
                    {},
                )
            )

            record.semantic_role, record.confidence = infer_semantic_role(
                class_name=record.class_name,
                variable_name=variable_name,
                object_name=record.object_name,
                properties=record.properties,
            )

            record.suggested_selectors = build_selectors(
                class_name=record.class_name,
                object_name=record.object_name,
                semantic_role=record.semantic_role,
            )

            record.notes = build_notes(
                record,
            )

            if variable_name in self.parent_variables:
                record.parent_variable = self.parent_variables[variable_name]

        return self.objects







def infer_semantic_role(
    *,
    class_name: str,
    variable_name: str,
    object_name: Optional[str],
    properties: dict,
) -> tuple[str, str]:

    candidates = []

    names = []

    if object_name:
        names.append(object_name.lower())

    names.append(variable_name.lower())

    combined = " ".join(names).replace("-", "_")





    for fragment, role in ROLE_RULES:

        normalized_fragment = fragment.lower().replace("-", "_")

        if normalized_fragment in combined:
            confidence = "high"


            if object_name and object_name.lower() == fragment.lower():
                confidence = "very_high"

            candidates.append(
                (
                    confidence,
                    role,
                )
            )

    if candidates:
        return choose_best_role(candidates)





    class_fallbacks = {
        "QLineEdit": ("text_input", "medium"),
        "QTextEdit": ("text_editor", "medium"),
        "QPlainTextEdit": ("text_editor", "medium"),
        "QComboBox": ("selector", "medium"),
        "QPushButton": ("button", "low"),
        "QToolButton": ("tool_button", "low"),
        "QCheckBox": ("checkbox", "medium"),
        "QRadioButton": ("radio_button", "medium"),
        "QListWidget": ("list", "medium"),
        "QTreeWidget": ("tree", "medium"),
        "QTableWidget": ("table", "medium"),
        "QTableView": ("table", "medium"),
        "QFrame": ("frame", "low"),
        "QWidget": ("container", "low"),
    }

    if class_name in class_fallbacks:
        return class_fallbacks[class_name]

    return "unclassified", "unknown"


def choose_best_role(
    candidates: list[tuple[str, str]],
) -> tuple[str, str]:

    confidence_rank = {
        "unknown": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "very_high": 4,
    }

    candidates = sorted(
        candidates,
        key=lambda item: (
            confidence_rank.get(item[0], 0),
            item[1],
        ),
        reverse=True,
    )

    confidence, role = candidates[0]

    return role, confidence







def build_selectors(
    *,
    class_name: str,
    object_name: Optional[str],
    semantic_role: str,
) -> list[str]:

    selectors: list[str] = []





    if semantic_role != "unclassified":
        selectors.append(f'{class_name}[role="{semantic_role}"]')








    if object_name:
        selectors.append(f"#{object_name}")







    selectors.append(class_name)

    return selectors







def build_notes(
    record: ObjectRecord,
) -> list[str]:

    notes = []

    if record.object_name is None:
        notes.append(
            "No setObjectName() detected; semantic styling should prefer "
            "a role property or class-level selector."
        )

    if record.semantic_role == "unclassified":
        notes.append("Review manually before adding a stylesheet rule.")

    if record.class_name in {
        "QPushButton",
        "QToolButton",
    }:
        notes.append(
            "Button is a candidate for a semantic role such as "
            "primary_action, secondary_action, danger, or icon_button."
        )

    if record.class_name in {
        "QLineEdit",
        "QTextEdit",
        "QPlainTextEdit",
        "QComboBox",
    }:
        notes.append(
            "Input/control can normally reuse the existing global " "input-control API."
        )

    if record.properties.get("fixed_height") is not None:
        notes.append(
            "Fixed height detected; verify whether this should remain "
            "component-specific or move into ResponsiveMetrics."
        )

    if record.properties.get("fixed_size") is not None:
        notes.append(
            "Fixed size detected; verify whether this should remain "
            "component-specific or move into ResponsiveMetrics."
        )

    return notes







def build_summary(
    records: list[ObjectRecord],
) -> dict:

    roles: dict[str, int] = {}
    classes: dict[str, int] = {}
    missing_names = []

    for record in records:
        classes[record.class_name] = classes.get(record.class_name, 0) + 1

        roles[record.semantic_role] = roles.get(record.semantic_role, 0) + 1

        if not record.object_name:
            missing_names.append(record.variable_name)

    return {
        "total_objects": len(records),
        "classes": dict(sorted(classes.items())),
        "semantic_roles": dict(sorted(roles.items())),
        "objects_without_object_name": sorted(missing_names),
    }


def extract_file(
    input_path: Path,
) -> tuple[list[ObjectRecord], dict]:

    source = input_path.read_text(encoding="utf-8")

    tree = ast.parse(
        source,
        filename=str(input_path),
    )

    extractor = UIObjectExtractor(source)

    extractor.visit(tree)

    records = extractor.finalize()

    summary = build_summary(records)

    return records, summary







def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically extract Qt UI objects and semantic roles "
            "from a Python source file."
        )
    )

    parser.add_argument(
        "input",
        nargs="?",
        default="chat_window.py",
        help="Python UI source file to inspect.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="JSON output path.",
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    input_path = Path(args.input).resolve()

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    if input_path.suffix.lower() != ".py":
        raise SystemExit("Input must be a Python source file.")

    records, summary = extract_file(input_path)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = input_path.parent / f"{input_path.stem}_objects.json"

    payload = {
        "schema_version": 1,
        "source_file": str(input_path),
        "summary": summary,
        "objects": [asdict(record) for record in records],
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )





    print()
    print("=" * 78)
    print("Qt UI OBJECT INVENTORY")
    print("=" * 78)
    print(f"Source : {input_path}")
    print(f"Output : {output_path}")
    print()

    print(f"Objects discovered : {summary['total_objects']}")

    print()
    print("Classes:")
    for class_name, count in summary["classes"].items():
        print(f"  {class_name:<24} {count}")

    print()
    print("Semantic roles:")
    for role, count in summary["semantic_roles"].items():
        print(f"  {role:<24} {count}")

    print()
    print("Objects:")
    print("-" * 78)

    for record in records:

        object_name = record.object_name if record.object_name else "<none>"

        parent = record.parent_variable if record.parent_variable else "<none>"

        print(
            f"{record.variable_name:<24} "
            f"{record.class_name:<18} "
            f"{object_name:<24} "
            f"{record.semantic_role:<24} "
            f"{record.confidence:<10}"
        )

        print(f"    parent={parent}")

        print(f"    selectors={record.suggested_selectors}")

    print()
    print("=" * 78)
    print("Objects without explicit objectName:")
    print("=" * 78)

    if summary["objects_without_object_name"]:
        for name in summary["objects_without_object_name"]:
            print(f"  - {name}")
    else:
        print("  None")

    print()
    print("No source files or stylesheets were modified.")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
