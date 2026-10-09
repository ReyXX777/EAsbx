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
from qt_theme.moon_activity import MoonActivity
from .filesystem_service import SandboxFilesystemService
from .filesystem_table import TableFormatter
from .filesystem_agent_events import FilesystemToolActivity


class FilesWorkspace(QWidget):
    """
    Qt-only filesystem workspace.

    Responsibilities:
        - Display the sandbox directory tree.
        - Allow directory navigation.
        - Preview selected files.
        - Display table-like files in a table.
        - Display text files in a text viewer.
        - Reflect filesystem-agent navigation and file access.

    The workspace does NOT execute filesystem operations itself.
    All filesystem access goes through SandboxFilesystemService.
    """

    file_opened = Signal(str)
    operation_error = Signal(str)

    def __init__(
        self,
        service: SandboxFilesystemService,
        parent=None,
    ):
        super().__init__(parent)

        self.service = service

        self._build_ui()

        self.refresh()





    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        root_layout.setSpacing(6)





        toolbar = QHBoxLayout()

        self.path_field = QLineEdit(".")
        self.path_field.setPlaceholderText("Sandbox-relative path")

        refresh_button = QPushButton("Refresh")

        refresh_button.setProperty(
            "role",
            "primary",
        )

        refresh_button.clicked.connect(self.refresh)

        toolbar.addWidget(QLabel("Path:"))

        toolbar.addWidget(
            self.path_field,
            1,
        )

        toolbar.addWidget(refresh_button)

        root_layout.addLayout(toolbar)

        activity_layout = QHBoxLayout()

        activity_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        activity_layout.setSpacing(8)

        self.agent_activity = MoonActivity(
            self,
        )

        self.agent_activity.setVisible(False)

        activity_layout.addWidget(
            self.agent_activity,
        )

        self.agent_activity_label = QLabel("Filesystem agent working...")

        self.agent_activity_label.setProperty(
            "role",
            "muted",
        )

        activity_layout.addWidget(
            self.agent_activity_label,
        )

        activity_layout.addStretch()

        root_layout.addLayout(
            activity_layout,
        )





        splitter = QSplitter(Qt.Horizontal)





        self.tree = QTreeWidget()

        self.tree.setHeaderLabels(
            [
                "Name",
                "Type",
                "Size",
            ]
        )

        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)


        self.tree.itemClicked.connect(self._on_tree_item_clicked)



        self.tree.itemDoubleClicked.connect(self._on_tree_double_clicked)

        splitter.addWidget(self.tree)





        right = QWidget()

        right_layout = QVBoxLayout(right)

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        right_layout.setSpacing(4)





        self.preview_header = QLabel("File Preview")

        self.preview_header.setObjectName("filesystemPreviewHeader")
        self.preview_header.setProperty(
            "role",
            "muted",
        )
        right_layout.addWidget(self.preview_header)








        from PySide6.QtWidgets import QStackedWidget

        self.preview_stack = QStackedWidget()





        self.empty_preview = QLabel("Select a file to preview it.")

        self.empty_preview.setAlignment(Qt.AlignCenter)

        self.empty_preview.setObjectName("filesystemEmptyPreview")

        self.preview_stack.addWidget(self.empty_preview)





        self.preview = QPlainTextEdit()

        self.preview.setReadOnly(True)

        self.preview.setObjectName("filesystemTextPreview")

        self.preview_stack.addWidget(self.preview)





        self.table = QTableWidget()

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.table.setObjectName("filesystemTablePreview")

        self.preview_stack.addWidget(self.table)

        right_layout.addWidget(
            self.preview_stack,
            1,
        )

        splitter.addWidget(right)





        splitter.setSizes(
            [
                300,
                700,
            ]
        )

        root_layout.addWidget(
            splitter,
            1,
        )


        self._show_empty_preview()





    def _show_empty_preview(self):
        """
        Show the lightweight empty state.

        No stale file content remains visible.
        """

        self.preview.clear()

        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        self.preview_header.setText("File Preview")

        self.preview_stack.setCurrentWidget(self.empty_preview)

    def _show_text_preview(
        self,
        relative_path: str,
        content: str,
    ):
        """
        Display normal text-file content.
        """

        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        self.preview_header.setText(f"Preview — {Path(relative_path).name}")

        self.preview.setPlainText(content)

        self.preview_stack.setCurrentWidget(self.preview)

    def _show_table_preview(
        self,
        relative_path: str,
        columns: list[str],
        rows: list[list[str]],
    ):
        """
        Display structured/tabular file content.
        """

        self.preview.clear()

        self.preview_header.setText(f"Preview — {Path(relative_path).name}")

        self._show_table(
            columns,
            rows,
        )

        self.preview_stack.setCurrentWidget(self.table)





    def refresh(self):
        """
        Refresh the directory tree for the current sandbox path.

        Refreshing the tree clears the old preview because the
        previously displayed file may no longer belong to the
        currently displayed directory.
        """

        self.tree.clear()

        self._show_empty_preview()

        path = self.path_field.text().strip() or "."

        result = self.service.list_directory(path)

        if not result.success:
            self.operation_error.emit(result.message)

            self.empty_preview.setText(result.message)

            return

        for entry in result.data:

            item = QTreeWidgetItem(
                [
                    entry.name,
                    ("Folder" if entry.is_directory else "File"),
                    ("" if entry.is_directory else str(entry.size)),
                ]
            )

            item.setData(
                0,
                Qt.UserRole,
                entry.relative_path,
            )

            item.setData(
                1,
                Qt.UserRole,
                entry.is_directory,
            )

            self.tree.addTopLevelItem(item)





    def _on_tree_item_clicked(
        self,
        item: QTreeWidgetItem,
        _column: int,
    ):
        """
        Single-click behavior.

        Files:
            Preview immediately.

        Directories:
            Only select them. Navigation still happens on
            double-click so accidental clicks do not constantly
            change the current directory.
        """

        relative_path = item.data(
            0,
            Qt.UserRole,
        )

        is_directory = item.data(
            1,
            Qt.UserRole,
        )

        if not relative_path:
            return

        if is_directory:
            self._show_empty_preview()
            return

        self.file_opened.emit(relative_path)

        self._preview_file(relative_path)

    def _on_tree_double_clicked(
        self,
        item: QTreeWidgetItem,
        _column: int,
    ):
        """
        Double-click behavior.

        Directories:
            Enter the directory.

        Files:
            Explicitly open/preview the file.
        """

        relative_path = item.data(
            0,
            Qt.UserRole,
        )

        is_directory = item.data(
            1,
            Qt.UserRole,
        )

        if not relative_path:
            return

        if is_directory:

            self.path_field.setText(relative_path)

            self.refresh()

            return

        self.file_opened.emit(relative_path)

        self._preview_file(relative_path)





    def _preview_file(
        self,
        relative_path: str,
    ):
        """
        Read and display a file through the filesystem service.

        No direct filesystem access occurs here.
        """

        relative_path = (
            str(relative_path)
            .replace(
                "\\",
                "/",
            )
            .strip()
        )

        if not relative_path:
            self._show_empty_preview()
            return

        suffix = Path(relative_path).suffix.lower()





        if suffix in {
            ".csv",
            ".json",
        }:

            result = self.service.read_table(relative_path)

            if result.success:

                try:
                    columns, rows = TableFormatter.normalized_rows(result.data)

                    self._show_table_preview(
                        relative_path,
                        columns,
                        rows,
                    )

                except Exception as exc:

                    message = (
                        "Unable to format table preview: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    self.operation_error.emit(message)

                    self._show_text_preview(
                        relative_path,
                        message,
                    )

            else:

                self.operation_error.emit(result.message)

                self._show_text_preview(
                    relative_path,
                    result.message,
                )

            return





        result = self.service.read_file(relative_path)

        if result.success:

            self._show_text_preview(
                relative_path,
                result.data,
            )

        else:

            self.operation_error.emit(result.message)

            self._show_text_preview(
                relative_path,
                result.message,
            )





    def _show_table(
        self,
        columns: list[str],
        rows: list[list[str]],
    ):
        """
        Populate the table preview.
        """

        self.table.clear()

        self.table.setColumnCount(len(columns))

        self.table.setHorizontalHeaderLabels(columns)

        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):

            for column_index, value in enumerate(row):

                item = QTableWidgetItem(str(value))

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.table.resizeColumnsToContents()






    def _start_agent_activity(self) -> None:
        """Show the indeterminate filesystem-agent activity indicator."""

        self.agent_activity.setVisible(True)

        self.agent_activity_label.setVisible(True)

        self.agent_activity.start()

    def _stop_agent_activity(self) -> None:
        """Hide the filesystem-agent activity indicator."""

        self.agent_activity.stop()

        self.agent_activity.setVisible(False)

        self.agent_activity_label.setVisible(False)





    def show_agent_activity(
        self,
        activity: FilesystemToolActivity,
    ) -> None:
        """
        Visually represent the filesystem operation currently
        being performed by the filesystem agent.

        The UI remains presentation-only. The agent itself
        performs the actual filesystem operation through the
        filesystem service/tool layer.
        """
        self._start_agent_activity()
        if activity.is_navigation:

            path = activity.path or "."

            self.show_agent_directory(path)

            return

        if activity.is_file_access:

            path = activity.path

            if path:

                self.show_agent_file(path)
            return

    def stop_agent_activity(self) -> None:
        """Stop and hide the filesystem-agent activity indicator."""

        self._stop_agent_activity()





    def show_agent_directory(
        self,
        relative_path: str,
    ) -> None:
        """
        Navigate the workspace to a directory currently being
        inspected by the filesystem agent.
        """

        relative_path = relative_path.strip() or "."

        self.path_field.setText(relative_path)

        self.refresh()





    def show_agent_file(
        self,
        relative_path: str,
    ) -> None:
        """
        Navigate to the file's parent directory, select the
        file in the tree, and display its content.

        This keeps the UI synchronized with filesystem-agent
        activity.
        """

        relative_path = relative_path.replace("\\", "/").strip()

        if not relative_path:
            return

        parent_path = str(Path(relative_path).parent).replace(
            "\\",
            "/",
        )

        if parent_path in {
            "",
            ".",
        }:
            parent_path = "."





        self.path_field.setText(parent_path)

        self.refresh()





        self._select_agent_entry(relative_path)





        self._preview_file(relative_path)





    def _select_agent_entry(
        self,
        relative_path: str,
    ) -> None:
        """
        Select and scroll to a tree item corresponding to a
        sandbox-relative path.
        """

        target = relative_path.replace("\\", "/").rstrip("/")

        for index in range(self.tree.topLevelItemCount()):

            item = self.tree.topLevelItem(index)

            item_path = item.data(
                0,
                Qt.UserRole,
            )

            if not item_path:
                continue

            item_path = str(item_path).replace("\\", "/").rstrip("/")

            if item_path == target:

                self.tree.setCurrentItem(item)

                item.setSelected(True)

                self.tree.scrollToItem(item)

                return
