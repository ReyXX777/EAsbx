# app_menu_bar.py
from PySide6.QtWidgets import QMenuBar, QWidget


class AppMenuBar(QMenuBar):
    """Custom Application Menu Bar providing agent diagnostics and status monitoring."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.main_window = parent
        self._init_menus()

    def _init_menus(self):
        # --------------------------------------------------------------
        # Agent
        # --------------------------------------------------------------

        agent_menu = self.addMenu("Agent")

        status_action = agent_menu.addAction("Diagnostics")

        status_action.setShortcut("Ctrl+D")

        status_action.triggered.connect(self.show_agent_status_dialog)

        # --------------------------------------------------------------
        # Observation
        # --------------------------------------------------------------

        observation_action = agent_menu.addAction("Observation")

        observation_action.setShortcut("Ctrl+Shift+O")

        observation_action.triggered.connect(self.show_observation_monitor)

    def show_agent_status_dialog(self):
        """Open the embedded agent diagnostics page."""

        if self.main_window is None or not hasattr(
            self.main_window,
            "show_agent_diagnostics",
        ):
            return

        self.main_window.show_agent_diagnostics()

    def show_observation_monitor(self):
        """Open the embedded task observation monitor."""

        if self.main_window is None or not hasattr(
            self.main_window,
            "show_observation_monitor",
        ):
            return

        self.main_window.show_observation_monitor()
