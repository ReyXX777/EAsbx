# main.py
import os
import sys

# MUST set CDP remote debugging port before initializing QApplication or importing QWebEngineView
CDP_PORT = 9222
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = str(CDP_PORT)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QWidget,
)

from agent_engine import AgentExecutionWorker
from agent_response_parser import AgentResponseParser
from app_menu_bar import AppMenuBar
from browser_window import BrowserWindowWidget
from chat_formatter import ChatMessageFormatter
from chat_window import ChatWindowWidget
from task_bar import TaskBarWidget
from task_models import Task


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cowork AI Agent Suite")
        self.resize(1200, 750)

        # 1. Attach Custom Menu Bar
        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)

        self.task_bar = TaskBarWidget()
        self.chat_window = ChatWindowWidget()
        self.browser_window = BrowserWindowWidget()

        splitter.addWidget(self.task_bar)
        splitter.addWidget(self.chat_window)
        splitter.addWidget(self.browser_window)
        splitter.setSizes([220, 500, 480])

        main_layout.addWidget(splitter)

        self.agent_worker = None
        self.current_task = None

        # Connect Signal Routing
        self.chat_window.task_created_signal.connect(self.handle_new_task)

    def get_agent_status(self) -> dict:
        """Endpoint called by AppMenuBar or UI widgets to query live agent state."""
        if hasattr(self, "agent_worker") and self.agent_worker is not None:
            return self.agent_worker.get_status()
        return {
            "status": "idle",
            "current_step": 0,
            "last_action": "No agent running",
            "error": None,
        }

    def handle_new_task(self, task_prompt: str):
        """
        Create the canonical Task and start its execution.

        MainWindow coordinates the components but does not own
        the task's lifecycle state.
        """
        if (
            self.agent_worker is not None
            and self.agent_worker.isRunning()
        ):
            error_html = ChatMessageFormatter.format_message(
                "error",
                "A task is already running. "
                "Cancel it before starting another task.",
            )

            self.chat_window.chat_display.append(error_html)
            return

        task = Task(prompt=task_prompt)

        self.current_task = task

        self.task_bar.task_list.addItem(
            f"📌 {task_prompt}"
        )
        sys_msg = ChatMessageFormatter.format_message(
            "system",
            f"Connecting browser agent to embedded Qt WebEngine over CDP (`http://127.0.0.1:{CDP_PORT}`)...",
        )
        self.chat_window.chat_display.append(sys_msg)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            err_msg = ChatMessageFormatter.format_message(
                "error", "GEMINI_API_KEY environment variable is missing."
            )
            self.chat_window.chat_display.append(err_msg)
            return

        # Pass cdp_url pointing to local Qt WebEngine instance
        cdp_url = f"http://127.0.0.1:{CDP_PORT}"
        self.agent_worker = AgentExecutionWorker(
            task,
            api_key,
            cdp_url=cdp_url,
        )
        self.agent_worker.step_updated.connect(self.on_agent_step)
        self.agent_worker.task_finished.connect(self.on_agent_finished)
        self.agent_worker.start()

    def on_agent_step(self, step_msg: str):
        agent_html = ChatMessageFormatter.format_message("agent", step_msg)
        self.chat_window.chat_display.append(agent_html)

    def on_agent_finished(self, result):
        # 1. Generate formatted HTML block from response parser
        parsed_content = AgentResponseParser.parse_and_format(
            result
        )

        # 2. Wrap system header card around parsed_content without escaping inner HTML
        header_html = ChatMessageFormatter.format_message(
            "system",
            "**Task execution finished.**"
        )

        # 3. Append header and pre-rendered parsed HTML into chat window
        self.chat_window.chat_display.append(header_html)
        self.chat_window.chat_display.append(parsed_content)
    def cancel_current_task(self):
        """
        Request cancellation of the currently running task.
        """

        if self.agent_worker is None:
            return

        self.agent_worker.cancel()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())