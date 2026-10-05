# app_menu_bar.py
from PySide6.QtWidgets import QMenuBar, QMessageBox, QWidget


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
        """Fetches status from main window and displays a diagnostic popup."""
        status_info = {
            "status": "idle",
            "current_step": 0,
            "last_action": "No agent running",
            "error": None,
        }

        # Query main window if available
        if (
            self.main_window
            and hasattr(self.main_window, "get_agent_status")
            and callable(self.main_window.get_agent_status)
        ):
            status_info = self.main_window.get_agent_status()

        # Format diagnostic message
        status_str = status_info.get("status", "unknown").upper()
        step_count = status_info.get("current_step", 0)
        last_act = status_info.get("last_action", "N/A")
        err = status_info.get("error", None)

        msg = (
            f"<b>Agent Status:</b> {status_str}<br>"
            f"<b>Steps Executed:</b> {step_count}<br>"
            f"<b>Last Action:</b> {last_act}"
        )

        if err:
            msg += f"<br><br><span style='color: red;'><b>Error:</b> {err}</span>"

        # Display popup dialog
        QMessageBox.information(self.main_window, "Agent Diagnostics", msg)
        # Display popup dialog
        QMessageBox.information(self.main_window, "Agent Diagnostics", msg)

    def show_observation_monitor(self):
        """Open the task observation monitor."""

        if self.main_window is None or not hasattr(
            self.main_window,
            "show_observation_monitor",
        ):
            QMessageBox.warning(
                self.main_window,
                "Observation Monitor",
                "Observation monitor is unavailable.",
            )
            return

        self.main_window.show_observation_monitor()
