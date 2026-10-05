# task_bar.py

from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
)
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
    - Allow the sidebar to collapse/expand without changing MainWindow's
      splitter architecture.

    Existing application code can continue using:

        self.task_bar.task_list.addItem(...)

    No task execution logic belongs here.

    Theme ownership
    ---------------
    This widget does not own application colors or a local stylesheet.
    Semantic Qt properties are exposed so the global qt_theme package can
    style the widget.

    Collapse ownership
    ------------------
    The sidebar owns its own collapsed/expanded presentation. MainWindow
    only needs to keep using TaskBarWidget inside the existing QSplitter.
    """

    new_task_requested = Signal()
    task_selected = Signal(str)
    collapsed_changed = Signal(bool)

    # Sidebar geometry.
    EXPANDED_WIDTH = 220
    COLLAPSED_WIDTH = 46

    # Short, responsive animation.
    COLLAPSE_ANIMATION_MS = 90

    STATUS_QUEUED = "Queued"
    STATUS_AWAITING_APPROVAL = "Awaiting Approval"
    STATUS_RUNNING = "Running"
    STATUS_COMPLETED = "Completed"
    STATUS_FAILED = "Failed"
    STATUS_CANCELLED = "Cancelled"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("TaskBarWidget")

        self._expanded_width = self.EXPANDED_WIDTH
        self._collapsed = False

        self.setMinimumWidth(self.EXPANDED_WIDTH)
        self.setMaximumWidth(self.EXPANDED_WIDTH)

        self._build_ui()
        self._connect_signals()
        self._initialize_theme_roles()
        self._initialize_collapse_animation()

    # =====================================================================
    # UI construction
    # =====================================================================

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.main_layout.setSpacing(8)

        # -------------------------------------------------------------
        # Sidebar control row
        # -------------------------------------------------------------

        self.control_bar = QWidget()
        self.control_bar.setObjectName("TaskBarControlBar")

        control_layout = QHBoxLayout(self.control_bar)

        control_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        control_layout.setSpacing(0)

        self.collapse_button = QPushButton("‹")
        self.collapse_button.setObjectName("TaskBarCollapseButton")
        self.collapse_button.setToolTip("Collapse task bar")
        self.collapse_button.setCursor(Qt.CursorShape.PointingHandCursor)

        control_layout.addStretch()
        control_layout.addWidget(self.collapse_button)

        self.main_layout.addWidget(self.control_bar)

        # -------------------------------------------------------------
        # Main sidebar content
        # -------------------------------------------------------------

        self.content_widget = QWidget()
        self.content_widget.setObjectName("TaskBarContent")

        content_layout = QVBoxLayout(self.content_widget)

        content_layout.setContentsMargins(
            6,
            0,
            6,
            6,
        )

        content_layout.setSpacing(12)

        # -------------------------------------------------------------
        # Header
        # -------------------------------------------------------------

        header = QWidget()
        header.setObjectName("TaskBarHeader")

        header_layout = QVBoxLayout(header)

        header_layout.setContentsMargins(
            2,
            2,
            2,
            0,
        )

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

        content_layout.addWidget(header)

        # -------------------------------------------------------------
        # New Task button
        # -------------------------------------------------------------

        self.new_task_btn = QPushButton()
        self.new_task_btn.setObjectName("NewTaskButton")

        self.new_task_btn.setText("+   New Task")

        self.new_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.new_task_btn.setMinimumHeight(42)

        content_layout.addWidget(self.new_task_btn)

        # -------------------------------------------------------------
        # Search / filter
        # -------------------------------------------------------------

        search_container = QFrame()
        search_container.setObjectName("SearchContainer")

        search_container.setProperty(
            "role",
            "panel",
        )

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

        content_layout.addWidget(search_container)

        # -------------------------------------------------------------
        # Active task section
        # -------------------------------------------------------------

        self.active_header = self._create_section_header(
            "ACTIVE",
            "●",
        )

        content_layout.addWidget(self.active_header)

        self.active_task_card = self._create_empty_active_card()

        content_layout.addWidget(self.active_task_card)

        # -------------------------------------------------------------
        # History section
        # -------------------------------------------------------------

        history_header = QWidget()
        history_header.setObjectName("HistoryHeader")

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

        content_layout.addWidget(history_header)

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

        content_layout.addWidget(
            self.task_list,
            stretch=1,
        )

        # -------------------------------------------------------------
        # Bottom agent status
        # -------------------------------------------------------------

        self.status_card = QFrame()
        self.status_card.setObjectName("StatusCard")

        self.status_card.setProperty(
            "role",
            "status",
        )

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

        self.status_indicator.setProperty(
            "role",
            "success",
        )

        self.status_text = QLabel("Agent ready")
        self.status_text.setObjectName("StatusText")

        self.status_text.setProperty(
            "role",
            "muted",
        )

        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        content_layout.addWidget(self.status_card)

        self.main_layout.addWidget(
            self.content_widget,
            stretch=1,
        )

    # =====================================================================
    # Theme roles
    # =====================================================================

    def _initialize_theme_roles(self):
        """
        Expose semantic styling roles to the global qt_theme stylesheet.

        No colors, fonts, or application stylesheet are defined here.
        """

        self.setProperty(
            "role",
            "panel",
        )

        self.content_widget.setProperty(
            "role",
            "surface",
        )

        self.workspace_label.setProperty(
            "role",
            "muted",
        )

        self.title_label.setProperty(
            "role",
            "title",
        )

        self.subtitle_label.setProperty(
            "role",
            "muted",
        )

        self.new_task_btn.setProperty(
            "role",
            "primary",
        )

        self.search_icon.setProperty(
            "role",
            "muted",
        )

        self.task_search.setProperty(
            "role",
            "input",
        )

        self.history_label.setProperty(
            "role",
            "muted",
        )

        self.history_count.setProperty(
            "role",
            "badge",
        )

        self.active_task_card.setProperty(
            "role",
            "success",
        )

        self.active_task_title.setProperty(
            "role",
            "title",
        )

        self.active_task_description.setProperty(
            "role",
            "muted",
        )

        self.collapse_button.setProperty(
            "role",
            "tool",
        )

    # =====================================================================
    # Collapse / expand
    # =====================================================================

    def _initialize_collapse_animation(self):
        self._width_animation = QPropertyAnimation(
            self,
            b"maximumWidth",
            self,
        )

        self._width_animation.setDuration(self.COLLAPSE_ANIMATION_MS)

        self._width_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._width_animation.finished.connect(self._on_collapse_animation_finished)

    def toggle_collapsed(self):
        """
        Toggle between expanded and collapsed sidebar states.
        """

        if self._width_animation.state() == QPropertyAnimation.State.Running:
            return

        if self._collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self):
        """
        Collapse the task sidebar to its compact control-only width.
        """

        if self._collapsed:
            return

        self._expanded_width = max(
            self.width(),
            self.EXPANDED_WIDTH,
        )

        self._collapsed = True

        self.content_widget.setVisible(False)

        self.collapse_button.setText("›")
        self.collapse_button.setToolTip("Expand task bar")

        self._set_width_limits(
            self.width(),
            self.COLLAPSED_WIDTH,
        )

        self._animate_width(
            self.COLLAPSED_WIDTH,
        )

        self.collapsed_changed.emit(True)

    def expand(self):
        """
        Expand the task sidebar back to its previous/default width.
        """

        if not self._collapsed:
            return

        target_width = max(
            self._expanded_width,
            self.EXPANDED_WIDTH,
        )

        self._collapsed = False

        self.content_widget.setVisible(True)

        self.collapse_button.setText("‹")
        self.collapse_button.setToolTip("Collapse task bar")

        self._set_width_limits(
            self.width(),
            target_width,
        )

        self._animate_width(
            target_width,
        )

        self.collapsed_changed.emit(False)

    def is_collapsed(self) -> bool:
        """
        Return whether the sidebar is currently collapsed.
        """

        return self._collapsed

    def _animate_width(
        self,
        target_width: int,
    ):
        start_width = self.width()

        self._width_animation.stop()

        self._width_animation.setStartValue(start_width)

        self._width_animation.setEndValue(target_width)

        self._width_animation.start()

    def _set_width_limits(
        self,
        minimum_width: int,
        maximum_width: int,
    ):
        self.setMinimumWidth(
            min(
                minimum_width,
                maximum_width,
            )
        )

        self.setMaximumWidth(
            max(
                minimum_width,
                maximum_width,
            )
        )

    def _on_collapse_animation_finished(self):
        if self._collapsed:
            self.setMinimumWidth(self.COLLAPSED_WIDTH)

            self.setMaximumWidth(self.COLLAPSED_WIDTH)

        else:
            target_width = max(
                self._expanded_width,
                self.EXPANDED_WIDTH,
            )

            self.setMinimumWidth(self.EXPANDED_WIDTH)

            self.setMaximumWidth(target_width)

    # =====================================================================
    # Signals
    # =====================================================================

    def _connect_signals(self):
        self.new_task_btn.clicked.connect(self._on_new_task_clicked)

        self.task_list.itemClicked.connect(self._on_task_selected)

        self.task_search.textChanged.connect(self._filter_tasks)

        self.collapse_button.clicked.connect(self.toggle_collapsed)

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
    # Helpers
    # =====================================================================

    def _create_section_header(
        self,
        title: str,
        indicator: str = "",
    ) -> QWidget:

        widget = QWidget()
        widget.setObjectName("SectionHeader")

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

            indicator_label.setProperty(
                "role",
                "success",
            )

            layout.addWidget(indicator_label)

        label = QLabel(title)

        label.setObjectName("SectionLabel")

        label.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(label)
        layout.addStretch()

        return widget

    def _create_empty_active_card(self):
        card = QFrame()

        card.setObjectName("ActiveTaskCard")

        card.setProperty(
            "role",
            "success",
        )

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

        title.setProperty(
            "role",
            "title",
        )

        description = QLabel("Your next agent task will appear here.")

        description.setObjectName("ActiveTaskDescription")

        description.setProperty(
            "role",
            "muted",
        )

        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        self.active_task_title = title
        self.active_task_description = description

        return card

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
        """

        task_text = task_text.strip()

        if not task_text:
            return
        status = self._normalize_status(status)

        item = QListWidgetItem()

        item.setData(
            Qt.ItemDataRole.UserRole,
            status,
        )

        self.task_list.addItem(item)

        self._set_task_item_widget(
            item,
            task_text,
            status,
        )

        widget = self.task_list.itemWidget(item)

        if widget is not None:
            item.setSizeHint(widget.sizeHint())
        self._update_history_count()
        return item

    def set_active_task(
        self,
        task_text: str,
        status: str = STATUS_RUNNING,
    ):
        """
        Set the currently active task and its lifecycle state.

        MainWindow owns the lifecycle decision. This method only updates
        the task-bar presentation.
        """

        task_text = task_text.strip()

        if not task_text:
            self.clear_active_task()
            return

        status = self._normalize_status(status)

        self.active_task_title.setText(task_text)

        self.active_task_description.setText(f"Agent status · {status}")

        self.set_agent_status(status)

        self.active_task_card.setProperty(
            "role",
            self._status_role(status),
        )

        self._refresh_widget_style(self.active_task_card)

    def update_task_status(
        self,
        item: QListWidgetItem,
        status: str,
    ):
        """
        Update the lifecycle state of a specific task-list item.

        This method owns only the UI update. MainWindow remains responsible
        for deciding when a lifecycle transition occurs.
        """

        if item is None:
            return

        status = self._normalize_status(status)

        widget = self.task_list.itemWidget(item)

        if widget is None:
            item.setData(
                Qt.ItemDataRole.UserRole,
                status,
            )
            return

        labels = widget.findChildren(QLabel)

        title = None
        status_indicator = None
        status_label = None

        for label in labels:
            object_name = label.objectName()

            if object_name == "TaskItemTitle":
                title = label

            elif object_name == "TaskStatusIndicator":
                status_indicator = label

            elif object_name == "TaskStatus":
                status_label = label

        item.setData(
            Qt.ItemDataRole.UserRole,
            status,
        )

        if status_indicator is not None:
            status_indicator.setText(self._status_indicator(status))

            status_indicator.setProperty(
                "role",
                self._status_role(status),
            )

            self._refresh_widget_style(status_indicator)

        if status_label is not None:
            status_label.setText(status)

            status_label.setProperty(
                "role",
                "muted",
            )

            self._refresh_widget_style(status_label)

        item.setSizeHint(widget.sizeHint())

    def mark_task_awaiting_approval(
        self,
        item: QListWidgetItem,
    ):
        """Mark a task as waiting for human approval."""

        self.update_task_status(
            item,
            self.STATUS_AWAITING_APPROVAL,
        )

    def mark_task_running(
        self,
        item: QListWidgetItem,
    ):
        """Mark a task as actively executing."""

        self.update_task_status(
            item,
            self.STATUS_RUNNING,
        )

    def mark_task_completed(
        self,
        item: QListWidgetItem,
    ):
        """Mark a task as successfully completed."""

        self.update_task_status(
            item,
            self.STATUS_COMPLETED,
        )

    def mark_task_failed(
        self,
        item: QListWidgetItem,
    ):
        """Mark a task as failed."""

        self.update_task_status(
            item,
            self.STATUS_FAILED,
        )

    def mark_task_cancelled(
        self,
        item: QListWidgetItem,
    ):
        """Mark a task as cancelled."""

        self.update_task_status(
            item,
            self.STATUS_CANCELLED,
        )

    def clear_active_task(self):
        """
        Reset the active task area.
        """

        self.active_task_title.setText("No active task")

        self.active_task_description.setText("Your next agent task will appear here.")

        self.status_text.setText("Agent ready")
        self.active_task_card.setProperty(
            "role",
            "success",
        )

        self._refresh_widget_style(self.active_task_card)

    def set_agent_status(
        self,
        status: str,
    ):
        """
        Update the small bottom status indicator.

        The status text is normalized so lifecycle terminology remains
        consistent throughout the task bar.
        """

        status = self._normalize_status(status)

        if status == self.STATUS_QUEUED:
            display_text = "Agent queued"

        elif status == self.STATUS_AWAITING_APPROVAL:
            display_text = "Awaiting approval"

        elif status == self.STATUS_RUNNING:
            display_text = "Agent running"

        elif status == self.STATUS_COMPLETED:
            display_text = "Agent completed"

        elif status == self.STATUS_FAILED:
            display_text = "Agent failed"

        elif status == self.STATUS_CANCELLED:
            display_text = "Agent cancelled"

        else:
            display_text = f"Agent {status.lower()}"

        self.status_text.setText(display_text)

        self.status_indicator.setProperty(
            "role",
            self._status_role(status),
        )

        self.status_text.setProperty(
            "role",
            self._status_role(status),
        )

        self._refresh_widget_style(self.status_indicator)
        self._refresh_widget_style(self.status_text)

    def _refresh_widget_style(
        self,
        widget: QWidget,
    ):
        """
        Re-polish a widget after changing a dynamic Qt theme property.
        """

        style = widget.style()

        style.unpolish(widget)
        style.polish(widget)

        widget.update()

    # =====================================================================
    # Task item rendering
    # =====================================================================
    # =====================================================================
    # Task item rendering
    # =====================================================================

    def _set_task_item_widget(
        self,
        item: QListWidgetItem,
        task_text: str,
        status: str,
    ):
        status = self._normalize_status(status)

        item.setData(
            Qt.ItemDataRole.UserRole,
            status,
        )
        widget = QFrame()

        widget.setObjectName("TaskItem")

        widget.setProperty(
            "role",
            "card",
        )

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

        title.setProperty(
            "role",
            "title",
        )

        title.setWordWrap(True)

        status_row = QWidget()

        status_row.setObjectName("TaskStatusRow")

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

        indicator.setProperty(
            "role",
            self._status_role(status),
        )

        status_label = QLabel(status)

        status_label.setObjectName("TaskStatus")

        status_label.setProperty(
            "role",
            "muted",
        )

        status_layout.addWidget(indicator)

        status_layout.addWidget(status_label)

        status_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(status_row)

        self.task_list.setItemWidget(
            item,
            widget,
        )

    @classmethod
    def _normalize_status(
        cls,
        status: str,
    ) -> str:
        """
        Convert supported lifecycle aliases into canonical task states.

        Unknown states are preserved as text so the task bar remains
        forward-compatible with future lifecycle states.
        """

        normalized = str(status).strip().lower()

        aliases = {
            "queued": cls.STATUS_QUEUED,
            "pending": cls.STATUS_QUEUED,
            "awaiting approval": cls.STATUS_AWAITING_APPROVAL,
            "awaiting_approval": cls.STATUS_AWAITING_APPROVAL,
            "approval": cls.STATUS_AWAITING_APPROVAL,
            "review": cls.STATUS_AWAITING_APPROVAL,
            "waiting": cls.STATUS_AWAITING_APPROVAL,
            "running": cls.STATUS_RUNNING,
            "executing": cls.STATUS_RUNNING,
            "active": cls.STATUS_RUNNING,
            "completed": cls.STATUS_COMPLETED,
            "complete": cls.STATUS_COMPLETED,
            "success": cls.STATUS_COMPLETED,
            "failed": cls.STATUS_FAILED,
            "failure": cls.STATUS_FAILED,
            "error": cls.STATUS_FAILED,
            "cancelled": cls.STATUS_CANCELLED,
            "canceled": cls.STATUS_CANCELLED,
            "cancelled by user": cls.STATUS_CANCELLED,
        }

        return aliases.get(
            normalized,
            status.strip() or cls.STATUS_QUEUED,
        )

    @classmethod
    def _status_role(
        cls,
        status: str,
    ) -> str:
        normalized = cls._normalize_status(status)

        if normalized in {
            cls.STATUS_RUNNING,
            cls.STATUS_COMPLETED,
        }:
            return "success"

        if normalized in {
            cls.STATUS_FAILED,
        }:
            return "danger"

        if normalized in {
            cls.STATUS_AWAITING_APPROVAL,
        }:
            return "warning"

        if normalized in {
            cls.STATUS_QUEUED,
            cls.STATUS_CANCELLED,
        }:
            return "muted"

        return "muted"

    @classmethod
    def _status_indicator(
        cls,
        status: str,
    ) -> str:
        normalized = cls._normalize_status(status)

        if normalized == cls.STATUS_RUNNING:
            return "●"

        if normalized == cls.STATUS_COMPLETED:
            return "✓"

        if normalized == cls.STATUS_FAILED:
            return "×"

        if normalized == cls.STATUS_AWAITING_APPROVAL:
            return "◐"

        if normalized == cls.STATUS_CANCELLED:
            return "⊘"

        if normalized == cls.STATUS_QUEUED:
            return "○"

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
            status=self.STATUS_QUEUED,
        )
