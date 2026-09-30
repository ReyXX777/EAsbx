from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .filesystem_models import FileEntry
from .filesystem_service import SandboxFilesystemService
from .filesystem_table import TableFormatter


class FilesWorkspace(QWidget):
    """
    Qt-only filesystem workspace.

    It is intentionally independent of BrowserWindowWidget. The existing
    BrowserWindowWidget can embed this widget into its `files_workspace`.
    """

    file_opened = Signal(str)
    operation_error = Signal(str)

    def __init__(self, service: SandboxFilesystemService, parent=None):
        super().__init__(parent)
        self.service = service
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        toolbar = QHBoxLayout()
        self.path_field = QLineEdit(".")
        self.path_field.setPlaceholderText("Sandbox-relative path")
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(QLabel("Path:"))
        toolbar.addWidget(self.path_field, 1)
        toolbar.addWidget(refresh_button)
        root_layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Size"])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_clicked)
        splitter.addWidget(self.tree)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Select a file to preview it.")
        right_layout.addWidget(self.preview, 2)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.table, 2)

        splitter.addWidget(right)
        splitter.setSizes([260, 500])
        root_layout.addWidget(splitter, 1)

    def refresh(self):
        self.tree.clear()
        path = self.path_field.text().strip() or "."
        result = self.service.list_directory(path)

        if not result.success:
            self.operation_error.emit(result.message)
            self.preview.setPlainText(result.message)
            return

        for entry in result.data:
            item = QTreeWidgetItem(
                [
                    entry.name,
                    "Folder" if entry.is_directory else "File",
                    "" if entry.is_directory else str(entry.size),
                ]
            )
            item.setData(0, Qt.UserRole, entry.relative_path)
            item.setData(1, Qt.UserRole, entry.is_directory)
            self.tree.addTopLevelItem(item)

    def _on_tree_double_clicked(self, item: QTreeWidgetItem, _column: int):
        relative_path = item.data(0, Qt.UserRole)
        is_directory = item.data(1, Qt.UserRole)

        if is_directory:
            self.path_field.setText(relative_path)
            self.refresh()
            return

        self.file_opened.emit(relative_path)
        self._preview_file(relative_path)

    def _preview_file(self, relative_path: str):
        suffix = Path(relative_path).suffix.lower()

        if suffix in {".csv", ".json"}:
            result = self.service.read_table(relative_path)
            if result.success:
                columns, rows = TableFormatter.normalized_rows(result.data)
                self._show_table(columns, rows)
                self.preview.clear()
            else:
                self.operation_error.emit(result.message)
                self.preview.setPlainText(result.message)
            return

        result = self.service.read_file(relative_path)
        if result.success:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.preview.setPlainText(result.data)
        else:
            self.operation_error.emit(result.message)
            self.preview.setPlainText(result.message)

    def _show_table(self, columns: list[str], rows: list[list[str]]):
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
