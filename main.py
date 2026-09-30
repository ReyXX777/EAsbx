# main.py

import os
import sys

# MUST set CDP remote debugging port before initializing QApplication
# or importing QWebEngineView.
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

from approval import (
    ApprovalEngine,
    ApprovalStatus,
    GeminiDecisionClassifier,
    ApprovalPolicyEngine,
)
from approval.schema_loader import ApprovalSchemaLoader


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cowork AI Agent Suite")
        self.resize(1200, 750)

        # ---------------------------------------------------------
        # 1. Menu bar
        # ---------------------------------------------------------

        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # ---------------------------------------------------------
        # 2. Main layout
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 3. Agent state
        # ---------------------------------------------------------

        self.agent_worker = None
        self.current_task = None

        # ---------------------------------------------------------
        # 4. Approval layer
        # ---------------------------------------------------------

        approval_schema_path = os.path.join(
            os.path.dirname(__file__),
            "schemas",
            "approval_schema.json",
        )

        approval_schema_loader = ApprovalSchemaLoader(approval_schema_path)

        self.approval_classifier = None
        self.approval_engine = None

        approval_api_key = os.getenv("GEMINI_API_KEY")

        if approval_api_key:
            self.approval_classifier = GeminiDecisionClassifier(
                api_key=approval_api_key,
                schema_loader=approval_schema_loader,
            )

            self.approval_engine = ApprovalEngine(
                classifier=self.approval_classifier,
                policy_engine=ApprovalPolicyEngine(),
            )

        # ---------------------------------------------------------
        # 5. Signal routing
        # ---------------------------------------------------------

        self.chat_window.task_created_signal.connect(self.handle_new_task)

    # =============================================================
    # Agent status
    # =============================================================

    def get_agent_status(self) -> dict:
        """
        Endpoint called by AppMenuBar or UI widgets to query
        live agent state.
        """

        if hasattr(self, "agent_worker") and self.agent_worker is not None:
            return self.agent_worker.get_status()

        return {
            "status": "idle",
            "current_step": 0,
            "last_action": "No agent running",
            "error": None,
        }

    # =============================================================
    # Task creation + approval
    # =============================================================

    def handle_new_task(self, task_prompt: str):
        """
        Create a canonical Task and pass it through the approval
        boundary before browser execution.

        MainWindow coordinates the UI and lifecycle routing.
        Authorization itself belongs to ApprovalEngine.
        """

        # ---------------------------------------------------------
        # 1. Prevent concurrent tasks
        # ---------------------------------------------------------

        if self.agent_worker is not None and self.agent_worker.isRunning():
            error_html = ChatMessageFormatter.format_message(
                "error",
                "A task is already running. " "Cancel it before starting another task.",
            )

            self.chat_window.chat_display.append(error_html)

            return

        # ---------------------------------------------------------
        # 2. Create canonical Task
        # ---------------------------------------------------------

        task = Task(prompt=task_prompt)

        self.current_task = task

        self.task_bar.task_list.addItem(f"📌 {task_prompt}")

        # ---------------------------------------------------------
        # 3. Approval layer availability check
        # ---------------------------------------------------------

        if self.approval_engine is None:
            error_html = ChatMessageFormatter.format_message(
                "error",
                "Approval engine is unavailable because "
                "GEMINI_API_KEY is not configured.",
            )

            self.chat_window.chat_display.append(error_html)

            return

        # ---------------------------------------------------------
        # 4. Inform UI that approval evaluation has started
        # ---------------------------------------------------------

        approval_started_html = ChatMessageFormatter.format_message(
            "system",
            "🔐 Evaluating task authorization...",
        )

        self.chat_window.chat_display.append(approval_started_html)

        # ---------------------------------------------------------
        # 5. Run approval classification + policy evaluation
        # ---------------------------------------------------------

        try:
            decision = self.approval_engine.evaluate(task_prompt)

        except Exception as exc:
            error_html = ChatMessageFormatter.format_message(
                "error",
                "Approval classification failed: " f"{type(exc).__name__}: {exc}",
            )

            self.chat_window.chat_display.append(error_html)

            return

        # ---------------------------------------------------------
        # 6. Display classification
        # ---------------------------------------------------------

        classification = decision.classification

        classification_msg = (
            "🔍 Approval classification:\n"
            f"- Operation: `{classification.operation_type}`\n"
            f"- Data sensitivity: "
            f"`{classification.data_sensitivity}`\n"
            f"- External side effect: "
            f"`{classification.external_side_effect}`\n"
            f"- Destructive: "
            f"`{classification.destructive}`\n"
            f"- Credential use: "
            f"`{classification.credential_use}`"
        )

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                classification_msg,
            )
        )

        # ---------------------------------------------------------
        # 7. Prepare policy reasons
        # ---------------------------------------------------------

        reasons = "\n".join(f"- {reason}" for reason in decision.reasons)

        # ---------------------------------------------------------
        # 8. DENY
        # ---------------------------------------------------------

        if decision.status == ApprovalStatus.DENY:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "🛑 Task denied by the local approval policy.\n" f"{reasons}",
                )
            )

            return

        # ---------------------------------------------------------
        # 9. REVIEW
        # ---------------------------------------------------------

        if decision.status == ApprovalStatus.REVIEW:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "system",
                    "⏸️ Human approval required before "
                    "browser execution.\n"
                    f"{reasons}",
                )
            )

            return

        # ---------------------------------------------------------
        # 10. APPROVED
        # ---------------------------------------------------------

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "✅ Task approved for browser execution.\n" f"{reasons}",
            )
        )

        # ---------------------------------------------------------
        # 11. Existing browser execution path
        # ---------------------------------------------------------

        sys_msg = ChatMessageFormatter.format_message(
            "system",
            "Connecting browser agent to embedded Qt WebEngine "
            f"over CDP (`http://127.0.0.1:{CDP_PORT}`)...",
        )

        self.chat_window.chat_display.append(sys_msg)

        # ---------------------------------------------------------
        # 12. Gemini API key for browser agent
        # ---------------------------------------------------------

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            err_msg = ChatMessageFormatter.format_message(
                "error",
                "GEMINI_API_KEY environment variable is missing.",
            )

            self.chat_window.chat_display.append(err_msg)

            return

        # ---------------------------------------------------------
        # 13. Connect browser-use to embedded Qt WebEngine
        # ---------------------------------------------------------

        cdp_url = f"http://127.0.0.1:{CDP_PORT}"

        # ---------------------------------------------------------
        # 14. Start browser agent worker
        # ---------------------------------------------------------

        self.agent_worker = AgentExecutionWorker(
            task,
            api_key,
            cdp_url=cdp_url,
        )

        self.agent_worker.step_updated.connect(self.on_agent_step)

        self.agent_worker.task_finished.connect(self.on_agent_finished)

        self.agent_worker.start()

    # =============================================================
    # Agent step updates
    # =============================================================

    def on_agent_step(self, step_msg: str):
        """
        Display live browser-agent execution updates.
        """

        agent_html = ChatMessageFormatter.format_message(
            "agent",
            step_msg,
        )

        self.chat_window.chat_display.append(agent_html)

    # =============================================================
    # Agent completion
    # =============================================================

    def on_agent_finished(self, result):
        """
        Display the final browser-agent execution result.
        """

        # Generate formatted HTML block from response parser.
        parsed_content = AgentResponseParser.parse_and_format(result)

        # Wrap system header card around parsed content
        # without escaping the inner HTML.
        header_html = ChatMessageFormatter.format_message(
            "system",
            "**Task execution finished.**",
        )

        self.chat_window.chat_display.append(header_html)

        self.chat_window.chat_display.append(parsed_content)

    # =============================================================
    # Task cancellation
    # =============================================================

    def cancel_current_task(self):
        """
        Request cancellation of the currently running task.
        """

        if self.agent_worker is None:
            return

        self.agent_worker.cancel()


# ================================================================
# Application entry point
# ================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
