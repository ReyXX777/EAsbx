

import os
import sys



CDP_PORT = 9222
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = str(CDP_PORT)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qt_theme import ThemeManager, ThemeMode

from agent_engine import AgentExecutionWorker
from agent_response_parser import AgentResponseParser
from filesystem.filesystem_worker import FilesystemExecutionWorker
from app_menu_bar import AppMenuBar
from browser_window import BrowserWindowWidget
from diagnostics_widget import DiagnosticsWidget
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





        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)





        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        main_layout.setSpacing(0)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("MainContentStack")





        self.chat_page = QWidget()
        self.chat_page.setObjectName("ChatPage")

        chat_layout = QHBoxLayout(self.chat_page)

        chat_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        chat_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        self.task_bar = TaskBarWidget()
        self.chat_window = ChatWindowWidget()
        self.browser_window = BrowserWindowWidget()

        splitter.addWidget(self.task_bar)
        splitter.addWidget(self.chat_window)
        splitter.addWidget(self.browser_window)

        splitter.setSizes(
            [
                220,
                500,
                480,
            ]
        )

        chat_layout.addWidget(splitter)

        self.content_stack.addWidget(
            self.chat_page,
        )





        self.diagnostics_page = QWidget()
        self.diagnostics_page.setObjectName("DiagnosticsPage")

        diagnostics_layout = QVBoxLayout(
            self.diagnostics_page,
        )

        diagnostics_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        diagnostics_layout.setSpacing(8)

        self.diagnostics_back_button = QPushButton(
            "← Back to Chat",
        )

        self.diagnostics_back_button.setObjectName(
            "DiagnosticsBackButton",
        )

        self.diagnostics_back_button.clicked.connect(
            self.show_chat_page,
        )

        self.diagnostics_widget = DiagnosticsWidget()

        diagnostics_layout.addWidget(
            self.diagnostics_back_button,
        )

        diagnostics_layout.addWidget(
            self.diagnostics_widget,
            1,
        )

        self.content_stack.addWidget(
            self.diagnostics_page,
        )




        self.observation_storage_root = os.path.join(
            os.path.dirname(__file__),
            "task_observation_data",
        )
        self.observation_page = QWidget()
        self.observation_page.setObjectName("ObservationPage")

        observation_layout = QVBoxLayout(
            self.observation_page,
        )

        observation_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        observation_layout.setSpacing(8)





        observation_navigation = QWidget()

        observation_navigation.setObjectName(
            "ObservationNavigation",
        )

        observation_navigation.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed,
        )

        observation_navigation_layout = QHBoxLayout(
            observation_navigation,
        )

        observation_navigation_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        observation_navigation_layout.setSpacing(0)

        self.observation_back_button = QPushButton(
            "← Back to Chat",
        )

        self.observation_back_button.setObjectName(
            "ObservationBackButton",
        )

        self.observation_back_button.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        self.observation_back_button.clicked.connect(
            self.show_chat_page,
        )

        observation_navigation_layout.addWidget(
            self.observation_back_button,
        )

        observation_layout.addWidget(
            observation_navigation,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )





        self.observation_monitor = ObservationWidget(
            storage_root=self.observation_storage_root,
        )

        observation_layout.addWidget(
            self.observation_monitor,
            1,
        )

        self.content_stack.addWidget(
            self.observation_page,
        )





        self.content_stack.setCurrentWidget(
            self.chat_page,
        )

        main_layout.addWidget(
            self.content_stack,
            1,
        )





        self.agent_worker = None
        self.active_agent_type = None
        self.current_task = None
        self.current_task_item = None
        self.pending_approval_task = None
        self.pending_approval_intent = None





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





        self.chat_window.task_created_signal.connect(self.handle_new_task)
        self.chat_window.approval_granted.connect(self.on_approval_granted)

        self.chat_window.approval_denied.connect(self.on_approval_denied)





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

    def show_chat_page(self):
        """Return the main content area to the Chat page."""

        self.content_stack.setCurrentWidget(
            self.chat_page,
        )

    def show_agent_diagnostics(self):
        """Show the embedded Agent Diagnostics page."""

        self.diagnostics_widget.refresh(
            self.get_agent_status(),
        )

        self.content_stack.setCurrentWidget(
            self.diagnostics_page,
        )

    def _ensure_observation_monitor(self):
        """Ensure the Observation Monitor widget exists."""

        if self.observation_monitor is not None:
            return

        self.observation_monitor = ObservationWidget(
            storage_root=self.observation_storage_root,
            parent=self.observation_page,
        )

        self.observation_page.layout().addWidget(
            self.observation_monitor,
            1,
        )

    def show_observation_monitor(self):
        """Show the embedded Observation Monitor page."""

        self._ensure_observation_monitor()

        self.observation_monitor.refresh()

        self.content_stack.setCurrentWidget(
            self.observation_page,
        )
        print(
            "DEBUG show_observation_monitor:",
            self.observation_monitor,
            type(self.observation_monitor),
        )





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





        task = Task(prompt=task_prompt)

        self.current_task = task

        self.current_task_item = self.task_bar.add_task(
            f"{task_prompt}",
            status=TaskBarWidget.STATUS_QUEUED,
        )
        self.task_bar.set_active_task(
            task_prompt,
            status="Queued",
        )





        if self.approval_engine is None:
            error_html = ChatMessageFormatter.format_message(
                "error",
                "Approval engine is unavailable because "
                "GEMINI_API_KEY is not configured.",
            )

            self.chat_window.chat_display.append(error_html)
            if self.current_task_item is not None:
                self.task_bar.mark_task_failed(self.current_task_item)

            self.task_bar.clear_active_task()

            self.current_task = None
            self.current_task_item = None
            self.task_bar.clear_active_task()
            return





        approval_started_html = ChatMessageFormatter.format_message(
            "system",
            "Evaluating task authorization...",
        )
        self.task_bar.set_active_task(
            task_prompt,
            status="Evaluating",
        )

        self.chat_window.chat_display.append(approval_started_html)





        try:
            decision = self.approval_engine.evaluate(task_prompt)

        except Exception as exc:
            error_html = ChatMessageFormatter.format_message(
                "error",
                "Approval classification failed: " f"{type(exc).__name__}: {exc}",
            )

            self.chat_window.chat_display.append(error_html)
            if self.current_task_item is not None:
                self.task_bar.mark_task_failed(self.current_task_item)

            self.task_bar.clear_active_task()

            self.current_task = None
            self.current_task_item = None
            return





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





        reasons = "\n".join(f"- {reason}" for reason in decision.reasons)





        if decision.status == ApprovalStatus.DENY:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Task denied by the local approval policy.\n" f"{reasons}",
                )
            )
            if self.current_task_item is not None:
                self.task_bar.mark_task_cancelled(self.current_task_item)

            self.task_bar.clear_active_task()

            self.current_task = None
            self.current_task_item = None

            return




        if decision.status == ApprovalStatus.REVIEW:



            self.pending_approval_task = (
                task,
                intent,
            )
            self.task_bar.set_active_task(
                task_prompt,
                status="Awaiting Approval",
            )

            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "system",
                    "Human approval required before "
                    "browser execution.\n"
                    f"{reasons}",
                )
            )






            self.chat_window.show_approval_request(decision)

            return





        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                (
                    f"Task approved for {intent.replace('_', ' ').title()}.\n"
                    f"{reasons}"
                ),
            )
        )
        self.task_bar.set_active_task(
            task_prompt,
            status="Running",
        )

        self.dispatch_task(task, intent)





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
        self.task_bar.set_active_task(
            task.prompt,
            status="Running",
        )
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
        if self.current_task_item is not None:
            self.task_bar.mark_task_failed(self.current_task_item)

        self.task_bar.clear_active_task()

        self.chat_window._reset_input_state()

        self.active_agent_type = None
        self.current_task = None
        self.current_task_item = None





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





        if self.agent_worker is not None and self.agent_worker.isRunning():
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "A browser task is already running.",
                )
            )

            return





        sys_msg = ChatMessageFormatter.format_message(
            "system",
            "Connecting browser agent to embedded Qt WebEngine "
            f"over CDP (`http://127.0.0.1:{CDP_PORT}`)...",
        )

        self.chat_window.chat_display.append(sys_msg)





        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            err_msg = ChatMessageFormatter.format_message(
                "error",
                "GEMINI_API_KEY environment variable is missing.",
            )

            self.chat_window.chat_display.append(err_msg)

            return





        cdp_url = f"http://127.0.0.1:{CDP_PORT}"





        self.agent_worker = AgentExecutionWorker(
            task,
            api_key,
            cdp_url=cdp_url,
        )
        self.active_agent_type = "BROWSER_AGENT"

        self.agent_worker.step_updated.connect(self.on_agent_step)

        self.agent_worker.task_finished.connect(self.on_agent_finished)

        self.agent_worker.start()





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





        if self.agent_worker is not None and self.agent_worker.isRunning():
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "Another agent task is already running.",
                )
            )

            if self.current_task_item is not None:
                self.task_bar.mark_task_failed(self.current_task_item)

            self.task_bar.clear_active_task()

            self.chat_window._reset_input_state()

            self.active_agent_type = None
            self.current_task = None
            self.current_task_item = None

            return





        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            self.chat_window.chat_display.append(
                ChatMessageFormatter.format_message(
                    "error",
                    "GEMINI_API_KEY environment variable is missing.",
                )
            )

            if self.current_task_item is not None:
                self.task_bar.mark_task_failed(self.current_task_item)

            self.task_bar.clear_active_task()

            self.chat_window._reset_input_state()

            self.active_agent_type = None
            self.current_task = None
            self.current_task_item = None

            return





        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "Starting Filesystem Agent inside " "the sandbox...",
            )
        )
        self.active_agent_type = "FILESYSTEM_AGENT"




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
                "Human approval granted. "
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

        if self.current_task_item is not None:
            self.task_bar.mark_task_cancelled(self.current_task_item)

        self.task_bar.clear_active_task()

        self.current_task = None
        self.current_task_item = None

        self.chat_window._reset_input_state()

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "Human approval denied. " "The task will not be executed.",
            )
        )





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





    def on_agent_finished(self, result):
        """
        Display the final browser-agent execution result.
        """


        parsed_content = AgentResponseParser.parse_and_format(result)



        header_html = ChatMessageFormatter.format_message(
            "system",
            "**Task execution finished.**",
        )

        self.chat_window.chat_display.append(header_html)

        self.chat_window.chat_display.append(parsed_content)

        if self.current_task_item is not None:
            self.task_bar.mark_task_completed(self.current_task_item)

        self.task_bar.clear_active_task()

        self.chat_window._reset_input_state()

        self.active_agent_type = None
        self.current_task = None
        self.current_task_item = None





    def on_filesystem_finished(self, result):
        """
        Display the final filesystem-agent response.
        """
        self.browser_window.stop_filesystem_agent_activity()
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
        if self.current_task_item is not None:
            self.task_bar.mark_task_completed(self.current_task_item)

        self.task_bar.clear_active_task()

        self.chat_window._reset_input_state()

        self.active_agent_type = None
        self.current_task = None
        self.current_task_item = None





    def on_filesystem_error(self, error_message: str):
        """
        Display filesystem-agent execution errors.
        """
        self.browser_window.stop_filesystem_agent_activity()

        self.chat_window.chat_display.append(
            ChatMessageFormatter.format_message(
                "error",
                f"Filesystem Agent Error: {error_message}",
            )
        )
        if self.current_task_item is not None:
            self.task_bar.mark_task_failed(self.current_task_item)

        self.task_bar.clear_active_task()

        self.chat_window._reset_input_state()

        self.active_agent_type = None
        self.current_task = None
        self.current_task_item = None





    def cancel_current_task(self):
        """
        Request cancellation of the currently running task.
        """

        if self.agent_worker is None:
            return

        self.agent_worker.cancel()

        if self.current_task_item is not None:
            self.task_bar.mark_task_cancelled(self.current_task_item)

        self.task_bar.clear_active_task()

        self.chat_window._reset_input_state()

        self.active_agent_type = None
        self.current_task = None
        self.current_task_item = None






if __name__ == "__main__":
    app = QApplication(sys.argv)

    ThemeManager.instance().apply(
        app,
        ThemeMode.DARK,
    )

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
