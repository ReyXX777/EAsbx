# task_bar.py

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TaskBarWidget(QFrame):
    """
    Agent task workspace sidebar.

    Responsibilities
    ----------------
    - Display the current and previous agent tasks.
    - Provide a clear entry point for creating a new task.
    - Provide lightweight task filtering.
    - Keep the task list compatible with MainWindow.

    Existing application code can continue using:

        self.task_bar.task_list.addItem(...)

    No task execution logic belongs here.
    """

    new_task_requested = Signal()
    task_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("TaskBarWidget")
        self.setMinimumWidth(210)
        self.setMaximumWidth(320)

        self._build_ui()
        self._connect_signals()
        self._apply_style()

    # =====================================================================
    # UI construction
    # =====================================================================

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        self.main_layout.setSpacing(12)

        # -------------------------------------------------------------
        # Header
        # -------------------------------------------------------------

        header = QWidget()
        header_layout = QVBoxLayout(header)

        header_layout.setContentsMargins(2, 2, 2, 0)
        header_layout.setSpacing(2)

        self.workspace_label = QLabel("WORKSPACE")
        self.workspace_label.setObjectName("WorkspaceLabel")

        self.title_label = QLabel("Agent Tasks")
        self.title_label.setObjectName("TitleLabel")

        self.subtitle_label = QLabel("Manage your agent sessions")
        self.subtitle_label.setObjectName("SubtitleLabel")

        header_layout.addWidget(self.workspace_label)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)

        self.main_layout.addWidget(header)

        # -------------------------------------------------------------
        # New Task button
        # -------------------------------------------------------------

        self.new_task_btn = QPushButton()

        self.new_task_btn.setObjectName("NewTaskButton")

        self.new_task_btn.setText("+   New Task")

        self.new_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.new_task_btn.setMinimumHeight(42)

        self.main_layout.addWidget(self.new_task_btn)

        # -------------------------------------------------------------
        # Search / filter
        # -------------------------------------------------------------

        search_container = QFrame()
        search_container.setObjectName("SearchContainer")

        search_layout = QHBoxLayout(search_container)

        search_layout.setContentsMargins(
            10,
            0,
            10,
            0,
        )

        search_layout.setSpacing(6)

        self.search_icon = QLabel("⌕")
        self.search_icon.setObjectName("SearchIcon")

        self.task_search = QLineEdit()

        self.task_search.setObjectName("TaskSearch")

        self.task_search.setPlaceholderText("Search tasks...")

        self.task_search.setClearButtonEnabled(True)

        search_layout.addWidget(self.search_icon)

        search_layout.addWidget(
            self.task_search,
            stretch=1,
        )

        self.main_layout.addWidget(search_container)

        # -------------------------------------------------------------
        # Active task section
        # -------------------------------------------------------------

        self.active_header = self._create_section_header(
            "ACTIVE",
            "●",
        )

        self.main_layout.addWidget(self.active_header)

        self.active_task_card = self._create_empty_active_card()

        self.main_layout.addWidget(self.active_task_card)

        # -------------------------------------------------------------
        # History section
        # -------------------------------------------------------------

        history_header = QWidget()

        history_layout = QHBoxLayout(history_header)

        history_layout.setContentsMargins(
            2,
            4,
            2,
            0,
        )

        history_layout.setSpacing(6)

        self.history_label = QLabel("TASK HISTORY")

        self.history_label.setObjectName("SectionLabel")

        self.history_count = QLabel("0")

        self.history_count.setObjectName("HistoryCount")

        history_layout.addWidget(self.history_label)

        history_layout.addStretch()

        history_layout.addWidget(self.history_count)

        self.main_layout.addWidget(history_header)

        # -------------------------------------------------------------
        # Task list
        # -------------------------------------------------------------

        self.task_list = QListWidget()

        self.task_list.setObjectName("TaskList")

        self.task_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        self.task_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

        self.task_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.task_list.setSpacing(5)

        self.task_list.setUniformItemSizes(False)

        self.main_layout.addWidget(
            self.task_list,
            stretch=1,
        )

        # -------------------------------------------------------------
        # Bottom agent status
        # -------------------------------------------------------------

        self.status_card = QFrame()

        self.status_card.setObjectName("StatusCard")

        status_layout = QHBoxLayout(self.status_card)

        status_layout.setContentsMargins(
            10,
            9,
            10,
            9,
        )

        status_layout.setSpacing(8)

        self.status_indicator = QLabel("●")

        self.status_indicator.setObjectName("StatusIndicator")

        self.status_text = QLabel("Agent ready")

        self.status_text.setObjectName("StatusText")

        status_layout.addWidget(self.status_indicator)

        status_layout.addWidget(self.status_text)

        status_layout.addStretch()

        self.main_layout.addWidget(self.status_card)

    # =====================================================================
    # Helpers
    # =====================================================================

    def _create_section_header(
        self,
        title: str,
        indicator: str = "",
    ) -> QWidget:

        widget = QWidget()

        layout = QHBoxLayout(widget)

        layout.setContentsMargins(
            2,
            2,
            2,
            0,
        )

        layout.setSpacing(6)

        if indicator:
            indicator_label = QLabel(indicator)

            indicator_label.setObjectName("ActiveIndicator")

            layout.addWidget(indicator_label)

        label = QLabel(title)

        label.setObjectName("SectionLabel")

        layout.addWidget(label)

        layout.addStretch()

        return widget

    def _create_empty_active_card(self):
        card = QFrame()

        card.setObjectName("ActiveTaskCard")

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            12,
            11,
            12,
            11,
        )

        layout.setSpacing(3)

        title = QLabel("No active task")

        title.setObjectName("ActiveTaskTitle")

        description = QLabel("Your next agent task will appear here.")

        description.setObjectName("ActiveTaskDescription")

        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        self.active_task_title = title
        self.active_task_description = description

        return card

    # =====================================================================
    # Signals
    # =====================================================================

    def _connect_signals(self):
        self.new_task_btn.clicked.connect(self._on_new_task_clicked)

        self.task_list.itemClicked.connect(self._on_task_selected)

        self.task_search.textChanged.connect(self._filter_tasks)

    def _on_new_task_clicked(self):
        self.new_task_requested.emit()

    def _on_task_selected(
        self,
        item: QListWidgetItem,
    ):
        if item is None:
            return

        self.task_selected.emit(item.text())

    # =====================================================================
    # Task management
    # =====================================================================

    def add_task(
        self,
        task_text: str,
        status: str = "Queued",
    ):
        """
        Add a task using the sidebar's own visual representation.

        This is optional for current MainWindow code, but provides a
        cleaner API for future task management.
        """

        task_text = task_text.strip()

        if not task_text:
            return

        item = QListWidgetItem()

        item.setData(
            Qt.ItemDataRole.UserRole,
            status,
        )

        item.setSizeHint(self._task_item_size())

        self.task_list.addItem(item)

        self._set_task_item_widget(
            item,
            task_text,
            status,
        )

        self._update_history_count()

    def set_active_task(
        self,
        task_text: str,
        status: str = "Running",
    ):
        """
        Update the active-task card.
        """

        self.active_task_title.setText(task_text)

        self.active_task_description.setText(f"Agent status · {status}")

        self.status_text.setText(f"Agent {status.lower()}")

    def clear_active_task(self):
        """
        Reset the active task area.
        """

        self.active_task_title.setText("No active task")

        self.active_task_description.setText("Your next agent task will appear here.")

        self.status_text.setText("Agent ready")

    def set_agent_status(
        self,
        status: str,
    ):
        """
        Update the small bottom status indicator.
        """

        status = status.strip()

        if not status:
            status = "Ready"

        self.status_text.setText(f"Agent {status.lower()}")

    # =====================================================================
    # Task item rendering
    # =====================================================================

    def _set_task_item_widget(
        self,
        item: QListWidgetItem,
        task_text: str,
        status: str,
    ):
        widget = QFrame()

        widget.setObjectName("TaskItem")

        layout = QVBoxLayout(widget)

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(3)

        title = QLabel(task_text)

        title.setObjectName("TaskItemTitle")

        title.setWordWrap(True)

        status_row = QWidget()

        status_layout = QHBoxLayout(status_row)

        status_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        status_layout.setSpacing(5)

        indicator = QLabel(self._status_indicator(status))

        indicator.setObjectName("TaskStatusIndicator")

        status_label = QLabel(status)

        status_label.setObjectName("TaskStatus")

        status_layout.addWidget(indicator)

        status_layout.addWidget(status_label)

        status_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(status_row)

        self.task_list.setItemWidget(
            item,
            widget,
        )

    def _task_item_size(self):
        return self.task_list.sizeHintForRow(QListWidgetItem())

    @staticmethod
    def _status_indicator(
        status: str,
    ) -> str:

        normalized = status.lower()

        if normalized in {
            "running",
            "executing",
            "active",
        }:
            return "●"

        if normalized in {
            "completed",
            "complete",
            "success",
        }:
            return "✓"

        if normalized in {
            "failed",
            "error",
            "denied",
        }:
            return "×"

        if normalized in {
            "review",
            "approval",
            "waiting",
        }:
            return "◐"

        return "○"

    # =====================================================================
    # Filtering
    # =====================================================================

    def _filter_tasks(
        self,
        search_text: str,
    ):
        query = search_text.strip().lower()

        for index in range(self.task_list.count()):

            item = self.task_list.item(index)

            widget = self.task_list.itemWidget(item)

            if widget is None:
                visible_text = item.text()
            else:
                labels = widget.findChildren(QLabel)

                visible_text = " ".join(label.text() for label in labels)

            item.setHidden(bool(query) and query not in visible_text.lower())

    # =====================================================================
    # Counters
    # =====================================================================

    def _update_history_count(self):
        self.history_count.setText(str(self.task_list.count()))

    # =====================================================================
    # Styling
    # =====================================================================

    def _apply_style(self):
        self.setStyleSheet("""
            /* =========================================================
               SIDEBAR
               ========================================================= */

            QFrame#TaskBarWidget {
                background-color: #f7f7f8;
                border: 1px solid #e4e4e7;
                border-radius: 12px;
            }

            /* =========================================================
               HEADER
               ========================================================= */

            QLabel#WorkspaceLabel {
                color: #8b8b93;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#TitleLabel {
                color: #18181b;
                font-size: 18px;
                font-weight: 700;
            }

            QLabel#SubtitleLabel {
                color: #8b8b93;
                font-size: 11px;
            }

            /* =========================================================
               NEW TASK
               ========================================================= */

            QPushButton#NewTaskButton {
                background-color: #18181b;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 9px 13px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#NewTaskButton:hover {
                background-color: #27272a;
            }

            QPushButton#NewTaskButton:pressed {
                background-color: #09090b;
                padding-top: 10px;
            }

            QPushButton#NewTaskButton:disabled {
                background-color: #d4d4d8;
                color: #71717a;
            }

            /* =========================================================
               SEARCH
               ========================================================= */

            QFrame#SearchContainer {
                background-color: white;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
                min-height: 34px;
            }

            QLabel#SearchIcon {
                color: #71717a;
                font-size: 18px;
            }

            QLineEdit#TaskSearch {
                background: transparent;
                border: none;
                color: #27272a;
                font-size: 12px;
                padding: 4px 0;
            }

            QLineEdit#TaskSearch:focus {
                border: none;
            }

            /* =========================================================
               SECTION LABELS
               ========================================================= */

            QLabel#SectionLabel {
                color: #71717a;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }

            QLabel#ActiveIndicator {
                color: #22c55e;
                font-size: 9px;
            }

            QLabel#HistoryCount {
                background-color: #e4e4e7;
                color: #52525b;
                border-radius: 8px;
                padding: 2px 7px;
                font-size: 9px;
                font-weight: 700;
            }

            /* =========================================================
               ACTIVE TASK
               ========================================================= */

            QFrame#ActiveTaskCard {
                background-color: white;
                border: 1px solid #e4e4e7;
                border-left: 3px solid #22c55e;
                border-radius: 8px;
            }

            QLabel#ActiveTaskTitle {
                color: #27272a;
                font-size: 12px;
                font-weight: 700;
            }

            QLabel#ActiveTaskDescription {
                color: #8b8b93;
                font-size: 10px;
            }

            /* =========================================================
               TASK LIST
               ========================================================= */

            QListWidget#TaskList {
                background: transparent;
                border: none;
                outline: none;
                padding: 0;
            }

            QListWidget#TaskList::item {
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }

            QListWidget#TaskList::item:selected {
                background: transparent;
            }

            QFrame#TaskItem {
                background-color: white;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
            }

            QFrame#TaskItem:hover {
                background-color: #fafafa;
                border-color: #d4d4d8;
            }

            QListWidget#TaskList::item:selected QFrame#TaskItem {
                background-color: #f4f4f5;
                border-color: #a1a1aa;
            }

            QLabel#TaskItemTitle {
                color: #27272a;
                font-size: 11px;
                font-weight: 600;
            }

            QLabel#TaskStatus {
                color: #8b8b93;
                font-size: 9px;
            }

            QLabel#TaskStatusIndicator {
                color: #71717a;
                font-size: 8px;
            }

            /* =========================================================
               STATUS CARD
               ========================================================= */

            QFrame#StatusCard {
                background-color: #18181b;
                border: none;
                border-radius: 8px;
            }

            QLabel#StatusIndicator {
                color: #22c55e;
                font-size: 9px;
            }

            QLabel#StatusText {
                color: #d4d4d8;
                font-size: 10px;
                font-weight: 600;
            }

            /* =========================================================
               SCROLLBAR
               ========================================================= */

            QListWidget#TaskList QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 2px 0;
            }

            QListWidget#TaskList QScrollBar::handle:vertical {
                background: #d4d4d8;
                border-radius: 3px;
                min-height: 30px;
            }

            QListWidget#TaskList QScrollBar::handle:vertical:hover {
                background: #a1a1aa;
            }

            QListWidget#TaskList QScrollBar::add-line:vertical,
            QListWidget#TaskList QScrollBar::sub-line:vertical {
                height: 0;
            }

            QListWidget#TaskList QScrollBar::add-page:vertical,
            QListWidget#TaskList QScrollBar::sub-page:vertical {
                background: transparent;
            }
            """)

    # =====================================================================
    # Public compatibility helpers
    # =====================================================================

    def add_legacy_task(
        self,
        task_text: str,
    ):
        """
        Compatibility helper for code that previously did:

            task_list.addItem(...)

        New code should preferably call add_task().
        """

        self.add_task(
            task_text,
            status="Queued",
        )
