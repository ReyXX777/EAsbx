# browser_window.py

from __future__ import annotations

from PySide6.QtCore import (
    QUrl,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QStackedWidget,
    QTabBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from filesystem.filesystem_service import SandboxFilesystemService
from filesystem.filesystem_workspace import FilesWorkspace
from filesystem.filesystem_agent_events import FilesystemToolActivity

# ---------------------------------------------------------
# Qt WebEngine
# ---------------------------------------------------------

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView

    WEBENGINE_AVAILABLE = True
except ImportError:
    QWebEngineView = None
    WEBENGINE_AVAILABLE = False


class BrowserTab(QWidget):
    """
    Individual browser tab.

    Keeps the browser page and its navigation state together.
    """

    title_changed = Signal(str)
    url_changed = Signal(QUrl)
    loading_changed = Signal(bool)

    def __init__(
        self,
        initial_url: str = "https://www.google.com",
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if WEBENGINE_AVAILABLE:
            self.browser_view = QWebEngineView()

            self.browser_view.titleChanged.connect(self._on_title_changed)

            self.browser_view.urlChanged.connect(self._on_url_changed)

            self.browser_view.loadStarted.connect(
                lambda: self.loading_changed.emit(True)
            )

            self.browser_view.loadFinished.connect(
                lambda _: self.loading_changed.emit(False)
            )

            self.browser_view.setUrl(QUrl(initial_url))

            layout.addWidget(self.browser_view)

        else:
            # Development fallback only.
            #
            # The actual application should run with Qt WebEngine.
            from PySide6.QtWidgets import QTextEdit

            self.browser_view = QTextEdit()
            self.browser_view.setReadOnly(True)
            self.browser_view.setPlainText(
                "Qt WebEngine is not available.\n\n"
                "Install PySide6-WebEngine to enable "
                "the embedded browser."
            )

            layout.addWidget(self.browser_view)

    def load_url(self, url: str):
        if not WEBENGINE_AVAILABLE:
            return

        self.browser_view.setUrl(QUrl(url))

    def reload_page(self):
        if WEBENGINE_AVAILABLE:
            self.browser_view.reload()

    def stop_loading(self):
        if WEBENGINE_AVAILABLE:
            self.browser_view.stop()

    def go_back(self):
        if WEBENGINE_AVAILABLE:
            self.browser_view.back()

    def go_forward(self):
        if WEBENGINE_AVAILABLE:
            self.browser_view.forward()

    def _on_title_changed(self, title: str):
        if not title:
            title = "New Tab"

        self.title_changed.emit(title)

    def _on_url_changed(self, url: QUrl):
        self.url_changed.emit(url)


class BrowserWindowWidget(QFrame):
    """
    Main browser workspace used by MOCKAPP.

    Responsibilities:
        - browser workspace navigation
        - browser tab management
        - URL navigation
        - browser state presentation
        - agent connection/status presentation

    It does NOT execute browser-agent tasks.
    """

    workspace_changed = Signal(str)
    url_navigated = Signal(str)

    browser_ready = Signal()
    browser_error = Signal(str)

    tab_created = Signal(int)
    tab_closed = Signal(int)

    # -----------------------------------------------------
    # Constructor
    # -----------------------------------------------------

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("browserWorkspace")

        self.setProperty("role", "panel")

        self._tabs: list[BrowserTab] = []

        self._build_ui()

        self._connect_signals()

        self._create_initial_tab()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)

        # -------------------------------------------------
        # Workspace header
        # -------------------------------------------------

        workspace_header = QFrame()
        workspace_header.setObjectName("workspaceHeader")
        workspace_header.setProperty("role", "panel")

        header_layout = QHBoxLayout(workspace_header)

        header_layout.setContentsMargins(
            10,
            6,
            10,
            6,
        )

        header_layout.setSpacing(8)

        self.workspace_tabs = QTabBar()

        self.workspace_tabs.setExpanding(False)
        self.workspace_tabs.setDrawBase(False)
        self.workspace_tabs.setDocumentMode(True)

        self.browser_workspace_index = self.workspace_tabs.addTab("🌐  Browser")

        self.files_workspace_index = self.workspace_tabs.addTab("📁  Files")

        header_layout.addWidget(self.workspace_tabs)

        header_layout.addStretch()

        # Agent status indicator

        self.agent_status_dot = QLabel("●")
        self.agent_status_dot.setObjectName("agentStatusDot")
        self.agent_status_dot.setProperty("status", "live")
        self.agent_status_label = QLabel("Agent Ready")

        self.agent_status_label.setObjectName("agentStatusLabel")
        self.agent_status_label.setProperty("role", "muted")
        self.agent_status_label.setProperty("status", "live")
        header_layout.addWidget(self.agent_status_dot)

        header_layout.addWidget(self.agent_status_label)

        main_layout.addWidget(workspace_header)

        # -------------------------------------------------
        # Browser workspace
        # -------------------------------------------------

        self.workspace_stack = QStackedWidget()

        # Browser page

        self.browser_workspace = QWidget()

        browser_layout = QVBoxLayout(self.browser_workspace)

        browser_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        browser_layout.setSpacing(0)

        # -------------------------------------------------
        # Navigation toolbar
        # -------------------------------------------------

        navigation_bar = QFrame()
        navigation_bar.setObjectName("navigationBar")
        navigation_bar.setProperty("role", "panel")

        navigation_layout = QHBoxLayout(navigation_bar)

        navigation_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        navigation_layout.setSpacing(4)

        self.back_btn = self._create_tool_button(
            "‹",
            "Go Back",
        )

        self.forward_btn = self._create_tool_button(
            "›",
            "Go Forward",
        )

        self.reload_btn = self._create_tool_button(
            "↻",
            "Reload",
        )

        self.stop_btn = self._create_tool_button(
            "×",
            "Stop Loading",
        )

        navigation_layout.addWidget(self.back_btn)

        navigation_layout.addWidget(self.forward_btn)

        navigation_layout.addWidget(self.reload_btn)

        navigation_layout.addWidget(self.stop_btn)

        # -------------------------------------------------
        # Address bar
        # -------------------------------------------------

        self.url_bar = QLineEdit()

        self.url_bar.setObjectName("addressBar")

        self.url_bar.setPlaceholderText("Search or enter a URL...")

        self.url_bar.setClearButtonEnabled(True)

        self.url_bar.returnPressed.connect(self.load_url)

        navigation_layout.addWidget(
            self.url_bar,
            stretch=1,
        )

        # Security / page menu

        self.page_menu_btn = QToolButton()

        self.page_menu_btn.setText("⋮")

        self.page_menu_btn.setToolTip("Page options")

        self.page_menu_btn.setAutoRaise(True)

        self.page_menu_btn.clicked.connect(self._show_page_menu)

        navigation_layout.addWidget(self.page_menu_btn)

        # New tab

        self.new_tab_btn = QToolButton()

        self.new_tab_btn.setText("+")

        self.new_tab_btn.setToolTip("New browser tab")

        self.new_tab_btn.setAutoRaise(True)

        self.new_tab_btn.clicked.connect(self.create_tab)

        navigation_layout.addWidget(self.new_tab_btn)

        browser_layout.addWidget(navigation_bar)

        # -------------------------------------------------
        # Browser tabs
        # -------------------------------------------------

        self.browser_tabs = QTabWidget()

        self.browser_tabs.setObjectName("browserTabs")

        self.browser_tabs.setDocumentMode(True)

        self.browser_tabs.setTabsClosable(True)

        self.browser_tabs.setMovable(True)

        self.browser_tabs.tabCloseRequested.connect(self.close_tab)

        self.browser_tabs.currentChanged.connect(self._on_current_tab_changed)

        browser_layout.addWidget(
            self.browser_tabs,
            stretch=1,
        )

        # -------------------------------------------------
        # Files workspace
        # -------------------------------------------------

        filesystem_root = r"X:\MOCKAPP\test_filesystem"

        self.filesystem_service = SandboxFilesystemService(filesystem_root)

        self.files_workspace = FilesWorkspace(
            service=self.filesystem_service,
            parent=self,
        )

        self.files_workspace.file_opened.connect(self._on_file_opened)

        self.files_workspace.operation_error.connect(self._on_filesystem_error)

        self.workspace_stack.addWidget(self.browser_workspace)

        self.workspace_stack.addWidget(self.files_workspace)

        main_layout.addWidget(
            self.workspace_stack,
            stretch=1,
        )

        # -------------------------------------------------
        # Browser status bar
        # -------------------------------------------------

        status_bar = QFrame()
        status_bar.setObjectName("browserStatusBar")
        status_bar.setProperty("role", "panel")

        status_layout = QHBoxLayout(status_bar)

        status_layout.setContentsMargins(
            10,
            4,
            10,
            4,
        )

        status_layout.setSpacing(8)

        self.connection_indicator = QLabel("●")

        self.connection_indicator.setObjectName("connectionIndicator")
        self.connection_indicator.setProperty("status", "live")
        self.connection_label = QLabel("Browser connected")

        self.connection_label.setObjectName("statusText")
        self.connection_label.setProperty("role", "muted")
        self.page_status_label = QLabel("Ready")

        self.page_status_label.setObjectName("statusText")
        self.page_status_label.setProperty("role", "muted")
        self.agent_activity_label = QLabel("Agent: Idle")

        self.agent_activity_label.setObjectName("statusText")
        self.agent_activity_label.setProperty("role", "muted")
        status_layout.addWidget(self.connection_indicator)

        status_layout.addWidget(self.connection_label)

        status_layout.addStretch()

        status_layout.addWidget(self.page_status_label)

        status_layout.addWidget(self.agent_activity_label)

        main_layout.addWidget(status_bar)

    # =====================================================
    # Signals
    # =====================================================

    def _connect_signals(self):

        self.workspace_tabs.currentChanged.connect(self._on_workspace_changed)
        self.back_btn.clicked.connect(self._go_back)

        self.forward_btn.clicked.connect(self._go_forward)

        self.reload_btn.clicked.connect(self._reload)

        self.stop_btn.clicked.connect(self._stop)

    # =====================================================
    # Tabs
    # =====================================================

    def _create_initial_tab(self):

        self.create_tab("https://www.google.com")

    def create_tab(
        self,
        url: str = "https://www.google.com",
    ):

        browser_tab = BrowserTab(
            initial_url=url,
            parent=self.browser_tabs,
        )

        index = self.browser_tabs.addTab(
            browser_tab,
            "New Tab",
        )

        self.browser_tabs.setCurrentIndex(index)

        self._tabs.append(browser_tab)

        browser_tab.title_changed.connect(
            lambda title, tab=browser_tab: self._update_tab_title(
                tab,
                title,
            )
        )

        browser_tab.url_changed.connect(
            lambda page_url, tab=browser_tab: self._on_tab_url_changed(
                tab,
                page_url,
            )
        )

        browser_tab.loading_changed.connect(self._on_loading_changed)

        self.tab_created.emit(index)

        return browser_tab

    def close_tab(self, index: int):

        if self.browser_tabs.count() <= 1:
            return

        widget = self.browser_tabs.widget(index)

        if widget in self._tabs:
            self._tabs.remove(widget)

        self.browser_tabs.removeTab(index)

        if widget:
            widget.deleteLater()

        self.tab_closed.emit(index)

    # =====================================================
    # Navigation
    # =====================================================

    def current_browser_tab(
        self,
    ) -> BrowserTab | None:

        widget = self.browser_tabs.currentWidget()

        if isinstance(
            widget,
            BrowserTab,
        ):
            return widget

        return None

    def load_url(self):

        url_text = self.url_bar.text().strip()

        if not url_text:
            return

        if "://" not in url_text:
            url_text = "https://" + url_text

        tab = self.current_browser_tab()

        if tab is None:
            return

        tab.load_url(url_text)

        self.url_navigated.emit(url_text)

    # =====================================================
    # Navigation button handlers
    # =====================================================

    def _go_back(self):

        tab = self.current_browser_tab()

        if tab:
            tab.go_back()

    def _go_forward(self):

        tab = self.current_browser_tab()

        if tab:
            tab.go_forward()

    def _reload(self):

        tab = self.current_browser_tab()

        if tab:
            tab.reload_page()

    def _stop(self):

        tab = self.current_browser_tab()

        if tab:
            tab.stop_loading()

    # =====================================================
    # Browser events
    # =====================================================

    def _on_current_tab_changed(
        self,
        index: int,
    ):

        tab = self.current_browser_tab()

        if tab is None:
            return

        current_url = tab.browser_view.url() if WEBENGINE_AVAILABLE else QUrl()

        self._on_tab_url_changed(
            tab,
            current_url,
        )

    def _on_tab_url_changed(
        self,
        tab: BrowserTab,
        url: QUrl,
    ):

        if tab != self.current_browser_tab():
            return

        self.url_bar.setText(url.toString())

        self.page_status_label.setText("Ready")

    def _on_title_changed(
        self,
        title: str,
    ):
        self.browser_ready.emit()

    def _update_tab_title(
        self,
        tab: BrowserTab,
        title: str,
    ):

        index = self.browser_tabs.indexOf(tab)

        if index < 0:
            return

        if len(title) > 22:
            title = title[:22] + "…"

        self.browser_tabs.setTabText(
            index,
            title or "New Tab",
        )

    def _on_loading_changed(
        self,
        loading: bool,
    ):

        if loading:
            self.page_status_label.setText("Loading...")

            self.connection_label.setText("Browser connected")

        else:
            self.page_status_label.setText("Ready")

    # =====================================================
    # Filesystem workspace
    # =====================================================

    def _on_file_opened(
        self,
        relative_path: str,
    ):
        self.set_agent_status("idle")

    def _on_filesystem_error(
        self,
        message: str,
    ):
        self.browser_error.emit(message)

    # =====================================================
    # Workspace
    # =====================================================

    def _on_workspace_changed(
        self,
        index: int,
    ):

        self.workspace_stack.setCurrentIndex(index)

        if index == self.browser_workspace_index:
            self.workspace_changed.emit("browser")

        elif index == self.files_workspace_index:
            self.workspace_changed.emit("files")

    # =====================================================
    # Agent state
    # =====================================================

    def set_agent_status(
        self,
        status: str,
    ):

        status = status.lower()

        labels = {
            "idle": "Agent Ready",
            "running": "Agent Working",
            "waiting": "Waiting for approval",
            "completed": "Agent Completed",
            "error": "Agent Error",
        }

        display_status = labels.get(
            status,
            status.title(),
        )

        self.agent_status_label.setText(display_status)

        self.agent_activity_label.setText(f"Agent: {display_status}")

        theme_status = {
            "idle": "live",
            "running": "running",
            "waiting": "running",
            "completed": "completed",
            "error": "failed",
        }.get(
            status,
            "live",
        )

        self._set_theme_property(
            self.agent_status_label,
            "status",
            theme_status,
        )

        self._set_theme_property(
            self.agent_status_dot,
            "status",
            theme_status,
        )

    def set_browser_connection_status(
        self,
        connected: bool,
        message: str | None = None,
    ):

        if connected:
            self.connection_indicator.setText("●")

            self.connection_label.setText(message or "Browser connected")

            self._set_theme_property(
                self.connection_indicator,
                "status",
                "live",
            )

        else:
            self.connection_indicator.setText("●")

            self.connection_label.setText(message or "Browser disconnected")

            self._set_theme_property(
                self.connection_indicator,
                "status",
                "failed",
            )

    # =====================================================
    # Context menu
    # =====================================================

    def _show_page_menu(self):

        menu = QMenu(self)

        reload_action = QAction(
            "Reload",
            self,
        )

        reload_action.triggered.connect(self._reload)

        menu.addAction(reload_action)

        stop_action = QAction(
            "Stop Loading",
            self,
        )

        stop_action.triggered.connect(self._stop)

        menu.addAction(stop_action)

        menu.addSeparator()

        new_tab_action = QAction(
            "New Tab",
            self,
        )

        new_tab_action.triggered.connect(self.create_tab)

        menu.addAction(new_tab_action)

        menu.exec(
            self.page_menu_btn.mapToGlobal(self.page_menu_btn.rect().bottomLeft())
        )

    def show_filesystem_agent_activity(
        self,
        activity: FilesystemToolActivity,
    ) -> None:
        """
        Present filesystem-agent activity in the Files workspace.

        BrowserWindowWidget acts as the UI coordinator. It does not
        execute filesystem operations itself.
        """

        self.set_agent_status("running")

        self.workspace_tabs.setCurrentIndex(self.files_workspace_index)

        self.workspace_stack.setCurrentIndex(self.files_workspace_index)

        self.files_workspace.show_agent_activity(activity)

    # =====================================================
    # Helpers
    # =====================================================
    @staticmethod
    def _set_theme_property(
        widget,
        name: str,
        value: str,
    ) -> None:

        widget.setProperty(name, value)

        style = widget.style()

        if style is not None:
            style.unpolish(widget)
            style.polish(widget)

        widget.update()

    @staticmethod
    def _create_tool_button(
        text: str,
        tooltip: str,
    ) -> QToolButton:

        button = QToolButton()

        button.setText(text)

        button.setToolTip(tooltip)

        button.setAutoRaise(True)

        return button
