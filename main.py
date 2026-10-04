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
from filesystem.filesystem_worker import FilesystemExecutionWorker
from app_menu_bar import AppMenuBar
from browser_window import BrowserWindowWidget
from chat_formatter import ChatMessageFormatter
from chat_window import ChatWindowWidget
from task_bar import TaskBarWidget
from task_models import Task
from task_observation_engine.task_observation import ObservationWidget

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
        self.active_agent_type = None
        self.current_task = None
        self.pending_approval_task = None
        self.pending_approval_intent = None

        self.observation_monitor = None

        self.observation_storage_root = os.path.join(
            os.path.dirname(__file__),
            "task_observation_data",
        )

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
        self.chat_window.approval_granted.connect(self.on_approval_granted)

        self.chat_window.approval_denied.connect(self.on_approval_denied)

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

    def show_observation_monitor(self):
        """Open or focus the task observation monitor."""

        if self.observation_monitor is None:
            observation_storage_root = os.path.join(
                os.path.dirname(__file__),
                "task_observation_data",
            )

            self.observation_monitor = ObservationWidget(
                storage_root=observation_storage_root,
            )

            self.observation_monitor.setWindowTitle("Observation Monitor")

            self.observation_monitor.resize(
                1200,
                750,
            )

        self.observation_monitor.show()
        self.observation_monitor.raise_()
        self.observation_monitor.activateWindow()

    # =============================================================
    # Task creation + approval
    # =============================================================

    def handle_new_task(
        self,
        intent: str,
        task_prompt: str,
    ):
        """
        Route a classified task to the appropriate agent.

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

        if self.pending_approval_task is not None:
            error_html = ChatMessageFormatter.format_message(
                "error",
                "A task is waiting for human approval. "
                "Approve or deny it before starting another task.",
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

            # Keep the canonical Task object alive while the
            # human approval UI is displayed.
            self.pending_approval_task = (
                task,
                intent,
            )

            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "system",
                    "⏸️ Human approval required before "
                    "browser execution.\n"
                    f"{reasons}",
                )
            )

            # Display the actual approval controls.
            #
            # The ChatWindow owns the presentation.
            # MainWindow remains responsible for deciding what
            # happens after Approve / Deny.
            self.chat_window.show_approval_request(decision)

            return

        # ---------------------------------------------------------
        # 10. APPROVED WITHOUT HUMAN REVIEW
        # ---------------------------------------------------------

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                (
                    f"✅ Task approved for {intent.replace('_', ' ').title()}.\n"
                    f"{reasons}"
                ),
            )
        )

        self.dispatch_task(task, intent)
        # =============================================================

    # Agent dispatch
    # =============================================================

    def dispatch_task(
        self,
        task: Task,
        intent: str,
    ):
        """
        Route an approved Task to the correct execution worker.

        MainWindow does not implement agent behavior.
        It only selects the appropriate agent boundary.
        """

        if task is None:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Cannot dispatch task: task is missing.",
                )
            )
            return

        if intent == "BROWSER_TASK":
            self.start_browser_task(task)
            return

        if intent == "FILESYSTEM_TASK":
            self.start_filesystem_task(task)
            return

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "error",
                f"Unsupported task intent: {intent}",
            )
        )

    # =============================================================
    # Browser task execution
    # =============================================================

    def start_browser_task(self, task: Task):
        """
        Start the browser agent for an approved Task.

        This method is intentionally separate from the approval
        system.

        It can be called by:

        1. The automatic ALLOW path.
        2. The human APPROVE path.

        Approval decisions are made before this method is called.
        """

        if task is None:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Cannot start browser task: task is missing.",
                )
            )

            return

        # ---------------------------------------------------------
        # Prevent concurrent browser execution
        # ---------------------------------------------------------

        if self.agent_worker is not None and self.agent_worker.isRunning():
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "A browser task is already running.",
                )
            )

            return

        # ---------------------------------------------------------
        # Inform UI
        # ---------------------------------------------------------

        sys_msg = ChatMessageFormatter.format_message(
            "system",
            "Connecting browser agent to embedded Qt WebEngine "
            f"over CDP (`http://127.0.0.1:{CDP_PORT}`)...",
        )

        self.chat_window.chat_display.append(sys_msg)

        # ---------------------------------------------------------
        # Gemini API key
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
        # Connect browser-use to embedded Qt WebEngine
        # ---------------------------------------------------------

        cdp_url = f"http://127.0.0.1:{CDP_PORT}"

        # ---------------------------------------------------------
        # Start browser agent worker
        # ---------------------------------------------------------

        self.agent_worker = AgentExecutionWorker(
            task,
            api_key,
            cdp_url=cdp_url,
        )
        self.active_agent_type = "BROWSER_AGENT"

        self.agent_worker.step_updated.connect(self.on_agent_step)

        self.agent_worker.task_finished.connect(self.on_agent_finished)

        self.agent_worker.start()

    # =============================================================
    # Filesystem task execution
    # =============================================================

    def start_filesystem_task(self, task):
        """
        Start the filesystem agent for an approved Task.

        The filesystem agent operates exclusively inside the
        application's sandbox filesystem.
        """

        if task is None:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Cannot start filesystem task: task is missing.",
                )
            )

            return

        # ---------------------------------------------------------
        # Prevent concurrent execution
        # ---------------------------------------------------------

        if self.agent_worker is not None and self.agent_worker.isRunning():
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Another agent task is already running.",
                )
            )

            return

        # ---------------------------------------------------------
        # Gemini API key
        # ---------------------------------------------------------

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "GEMINI_API_KEY environment variable is missing.",
                )
            )

            return

        # ---------------------------------------------------------
        # Inform UI
        # ---------------------------------------------------------

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "🗂️ Starting Filesystem Agent inside " "the sandbox...",
            )
        )
        self.active_agent_type = "FILESYSTEM_AGENT"
        # ---------------------------------------------------------
        # Start filesystem worker
        # ---------------------------------------------------------

        self.agent_worker = FilesystemExecutionWorker(
            task=task,
            api_key=api_key,
        )

        self.agent_worker.step_updated.connect(self.on_agent_step)
        self.agent_worker.tool_started.connect(
            self.browser_window.show_filesystem_agent_activity
        )
        self.agent_worker.task_finished.connect(self.on_filesystem_finished)

        self.agent_worker.error_occurred.connect(self.on_filesystem_error)

        self.agent_worker.start()

    # =============================================================
    # Human approval
    # =============================================================

    def on_approval_granted(self):
        """
        Continue execution after the human presses Approve.
        """

        pending = self.pending_approval_task

        if pending is None:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Approval was granted, but no pending task exists.",
                )
            )

            return

        self.pending_approval_task = None

        task, intent = pending

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "✅ Human approval granted. "
                f"Starting {intent.replace('_', ' ').title()}...",
            )
        )

        self.dispatch_task(
            task,
            intent,
        )

    def on_approval_denied(self):
        """
        Stop the pending task after the human presses Deny.
        """

        self.pending_approval_task = None

        self.current_task = None

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "🛑 Human approval denied. " "The task will not be executed.",
            )
        )

    # =============================================================
    # Agent step updates
    # =============================================================

    def on_agent_step(self, step_msg: str):
        """
        Display a step update from the active agent.

        Agent workers are responsible for identifying themselves.
        MainWindow only presents the emitted message.
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
        self.active_agent_type = None

    # =============================================================
    # Filesystem completion
    # =============================================================

    def on_filesystem_finished(self, result):
        """
        Display the final filesystem-agent response.
        """

        final_text = ""

        if isinstance(result, dict):
            final_text = result.get(
                "final_text",
                "",
            )

        if not final_text:
            final_text = "Filesystem task completed successfully."

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "**Filesystem task finished.**",
            )
        )

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "agent",
                final_text,
            )
        )
        self.active_agent_type = None

    # =============================================================
    # Filesystem errors
    # =============================================================

    def on_filesystem_error(self, error_message: str):
        """
        Display filesystem-agent execution errors.
        """

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "error",
                f"Filesystem Agent Error: {error_message}",
            )
        )
        self.active_agent_type = None

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
