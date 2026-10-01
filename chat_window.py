from __future__ import annotations

import json
import os

from google import genai
from google.genai import types

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from approval.approval_widget import ApprovalWidget
from approval.models import ApprovalDecision
from chat_formatter import ChatMessageFormatter

# ============================================================================
# Gemini Worker
# ============================================================================


class GeminiWorker(QThread):
    """
    Background Gemini worker.

    Responsibilities:
        1. Classify the user's message as CHAT, BROWSER_TASK,
           or FILESYSTEM_TASK.
        2. Stream normal chat responses.
        3. Emit executable tasks to the main application together
           with their classified intent.
        4. The worker performs no UI operations directly.
    """

    # Normal conversational response.
    chat_chunk = Signal(str)
    chat_finished = Signal()

    # Executable task:
    #   argument 1 -> intent
    #   argument 2 -> task description
    task_response = Signal(str, str)

    # Worker-level errors.
    error_occurred = Signal(str)

    def __init__(
        self,
        prompt: str,
        api_key: str,
        chat_session=None,
    ):
        super().__init__()

        self.prompt = prompt
        self.api_key = api_key
        self.chat_session = chat_session

    def run(self):
        try:
            # ==============================================================
            # 1. Create Gemini client
            # ==============================================================

            client = genai.Client(
                api_key=self.api_key,
            )

            # ==============================================================
            # 2. Load intent schema
            # ==============================================================

            schema_path = os.path.join(
                os.path.dirname(__file__),
                "intent_schema.json",
            )

            response_schema = None

            if os.path.exists(schema_path):
                with open(
                    schema_path,
                    "r",
                    encoding="utf-8",
                ) as file:
                    response_schema = json.load(file)

            # ==============================================================
            # 3. Intent classification instructions
            # ==============================================================

            system_instruction = (
                "You are an intent classification system for an AI assistant.\n"
                "\n"
                "Your ONLY job is to classify the user's message as exactly "
                "one of: 'CHAT', 'BROWSER_TASK', or 'FILESYSTEM_TASK'.\n"
                "\n"
                # ----------------------------------------------------------
                # Browser tasks
                # ----------------------------------------------------------
                "Use 'BROWSER_TASK' when the request requires the application "
                "to perform actions in a web browser, including:\n"
                "- opening a website\n"
                "- navigating to a URL\n"
                "- searching the web\n"
                "- clicking elements\n"
                "- filling forms\n"
                "- submitting forms\n"
                "- scraping or reading live web content\n"
                "- interacting with a web application\n"
                "- changing information on a website\n"
                "\n"
                # ----------------------------------------------------------
                # Filesystem tasks
                # ----------------------------------------------------------
                "Use 'FILESYSTEM_TASK' when the request requires the application "
                "to operate on files or directories in the application's "
                "sandboxed filesystem, including:\n"
                "- listing directories\n"
                "- searching for files\n"
                "- reading files\n"
                "- reading CSV or JSON tables\n"
                "- calculating values from filesystem data\n"
                "- creating files or directories\n"
                "- writing or editing files\n"
                "- copying or moving files\n"
                "- deleting files or directories\n"
                "\n"
                # ----------------------------------------------------------
                # Normal chat
                # ----------------------------------------------------------
                "Use 'CHAT' when the user is asking for:\n"
                "- general conversation\n"
                "- explanations\n"
                "- coding help\n"
                "- summarization\n"
                "- reasoning\n"
                "- writing\n"
                "- questions that do not require live browser interaction "
                "or filesystem operations\n"
                "\n"
                # ----------------------------------------------------------
                # Mixed requests
                # ----------------------------------------------------------
                "If the request requires browser interaction, classify it "
                "as 'BROWSER_TASK'.\n"
                "\n"
                "If the request requires filesystem operations, classify it "
                "as 'FILESYSTEM_TASK'.\n"
                "\n"
                "If a request contains both browser interaction and "
                "filesystem operations, classify it according to the "
                "primary action explicitly requested by the user.\n"
                "\n"
                # ----------------------------------------------------------
                # Output contract
                # ----------------------------------------------------------
                "Return ONLY JSON matching the supplied response schema."
            )

            # ==============================================================
            # 4. Build classification configuration
            # ==============================================================

            config_kwargs = {
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
            }

            if response_schema is not None:
                config_kwargs["response_schema"] = response_schema

            config = types.GenerateContentConfig(
                **config_kwargs,
            )

            # ==============================================================
            # 5. Ask Gemini to classify the message
            # ==============================================================

            classification_prompt = (
                "Classify the following user message:\n\n" f"{self.prompt}"
            )

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=classification_prompt,
                config=config,
            )

            # ==============================================================
            # 6. Validate Gemini response
            # ==============================================================

            if not response.text:
                raise ValueError("Gemini returned an empty intent classification.")

            try:
                data = json.loads(
                    response.text,
                )

            except json.JSONDecodeError as exc:
                raise ValueError(
                    "Gemini returned invalid JSON for intent classification."
                ) from exc

            if not isinstance(data, dict):
                raise ValueError("Gemini intent classification must be a JSON object.")

            # ==============================================================
            # 7. Extract classification
            # ==============================================================

            intent = (
                str(
                    data.get(
                        "intent",
                        "CHAT",
                    )
                )
                .strip()
                .upper()
            )

            task_desc = data.get(
                "task_description",
                self.prompt,
            )

            if not isinstance(task_desc, str) or not task_desc.strip():
                task_desc = self.prompt

            task_desc = task_desc.strip()

            # ==============================================================
            # 8. Validate intent
            # ==============================================================

            valid_intents = {
                "CHAT",
                "BROWSER_TASK",
                "FILESYSTEM_TASK",
            }

            if intent not in valid_intents:
                raise ValueError(f"Unknown intent returned by Gemini: {intent}")

            # ==============================================================
            # 9. Executable task
            # ==============================================================

            if intent in {
                "BROWSER_TASK",
                "FILESYSTEM_TASK",
            }:

                self.task_response.emit(
                    intent,
                    task_desc,
                )

                return

            # ==============================================================
            # 10. Normal chat
            # ==============================================================

            if self.chat_session is None:

                chat = client.chats.create(
                    model="gemini-3.5-flash-lite",
                )

            else:

                chat = self.chat_session

            # ==============================================================
            # 11. Stream Gemini conversation response
            # ==============================================================

            response_stream = chat.send_message_stream(
                self.prompt,
            )

            for chunk in response_stream:

                if chunk.text:
                    self.chat_chunk.emit(
                        chunk.text,
                    )

            # ==============================================================
            # 12. Chat completed
            # ==============================================================

            self.chat_finished.emit()

        except Exception as exc:

            self.error_occurred.emit(f"{type(exc).__name__}: {exc}")


# ============================================================================
# Chat Window
# ============================================================================


class ChatWindowWidget(QFrame):
    """
    Main conversational interface for the agentic workspace.

    This widget owns:
        - Conversation display
        - User composer
        - Chat mode selector
        - Approval UI presentation
        - Gemini worker lifecycle

    It does NOT own:
        - Browser execution
        - Approval policy
        - Task authorization logic
    """

    task_created_signal = Signal(str, str)

    approval_granted = Signal()
    approval_denied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.worker = None

        self.current_response_text = ""
        self.is_first_chunk = True

        self.current_approval_widget = None

        self._build_ui()
        self._apply_styles()

    # ========================================================================
    # UI Construction
    # ========================================================================

    def _build_ui(self):
        """
        Build the complete chat interface.
        """

        self.setObjectName("chatWindow")
        self.setFrameShape(QFrame.NoFrame)

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)

        # --------------------------------------------------------------------
        # Header
        # --------------------------------------------------------------------

        self.header = self._build_header()
        main_layout.addWidget(self.header)

        # --------------------------------------------------------------------
        # Conversation area
        # --------------------------------------------------------------------

        self.chat_display = QTextEdit()

        self.chat_display.setObjectName("chatDisplay")

        self.chat_display.setReadOnly(True)

        self.chat_display.setAcceptRichText(True)

        self.chat_display.setFrameShape(QFrame.NoFrame)

        self.chat_display.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.chat_display.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.chat_display.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        main_layout.addWidget(
            self.chat_display,
            stretch=1,
        )

        # --------------------------------------------------------------------
        # Approval region
        # --------------------------------------------------------------------

        self.approval_container = QWidget()

        self.approval_container.setObjectName("approvalContainer")

        self.approval_container.setVisible(False)

        self.approval_layout = QVBoxLayout(self.approval_container)

        self.approval_layout.setContentsMargins(
            16,
            8,
            16,
            12,
        )

        self.approval_layout.setSpacing(0)

        main_layout.addWidget(self.approval_container)

        # --------------------------------------------------------------------
        # Composer
        # --------------------------------------------------------------------

        self.composer = self._build_composer()

        main_layout.addWidget(self.composer)

    # ========================================================================
    # Header
    # ========================================================================

    def _build_header(self) -> QWidget:
        """
        Build the agent header.
        """

        header = QFrame()

        header.setObjectName("chatHeader")

        header.setFixedHeight(64)

        layout = QHBoxLayout(header)

        layout.setContentsMargins(
            18,
            10,
            18,
            10,
        )

        layout.setSpacing(12)

        # Agent icon
        icon = QLabel("✦")

        icon.setObjectName("agentIcon")

        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon.setFixedSize(
            36,
            36,
        )

        layout.addWidget(icon)

        # Title / subtitle
        title_layout = QVBoxLayout()

        title_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        title_layout.setSpacing(1)

        self.agent_title = QLabel("Cowork Agent")

        self.agent_title.setObjectName("agentTitle")

        self.agent_status = QLabel("Ready")

        self.agent_status.setObjectName("agentStatus")

        title_layout.addWidget(self.agent_title)

        title_layout.addWidget(self.agent_status)

        layout.addLayout(title_layout)

        layout.addStretch()

        # Small status indicator
        self.status_indicator = QLabel("●")

        self.status_indicator.setObjectName("statusIndicator")

        layout.addWidget(self.status_indicator)

        self.new_chat_btn = QPushButton("New chat")

        self.new_chat_btn.setObjectName("headerButton")

        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.new_chat_btn.clicked.connect(self.clear_conversation)

        layout.addWidget(self.new_chat_btn)

        return header

    # ========================================================================
    # Composer
    # ========================================================================

    def _build_composer(self) -> QWidget:
        """
        Build the modern agent composer.
        """

        outer = QFrame()

        outer.setObjectName("composerOuter")

        outer_layout = QVBoxLayout(outer)

        outer_layout.setContentsMargins(
            14,
            10,
            14,
            14,
        )

        outer_layout.setSpacing(8)

        # --------------------------------------------------------------
        # Main input card
        # --------------------------------------------------------------

        input_card = QFrame()

        input_card.setObjectName("inputCard")

        input_layout = QHBoxLayout(input_card)

        input_layout.setContentsMargins(
            10,
            7,
            8,
            7,
        )

        input_layout.setSpacing(6)

        # Add / attachment button
        self.add_btn = QPushButton("+")

        self.add_btn.setObjectName("composerIconButton")

        self.add_btn.setToolTip("Add files or context")

        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_btn.setFixedSize(
            34,
            34,
        )

        # Text input
        self.input_field = QLineEdit()

        self.input_field.setObjectName("messageInput")

        self.input_field.setPlaceholderText("Ask the agent to do something...")

        self.input_field.setClearButtonEnabled(False)

        self.input_field.returnPressed.connect(self.send_message)

        input_layout.addWidget(self.add_btn)

        input_layout.addWidget(
            self.input_field,
            stretch=1,
        )

        # Mode selector
        self.mode_dropdown = QComboBox()

        self.mode_dropdown.setObjectName("modeDropdown")

        self.mode_dropdown.addItems(
            [
                "Auto",
                "Manual",
                "Step-by-Step",
            ]
        )

        self.mode_dropdown.setToolTip("Agent execution mode")

        self.mode_dropdown.setMinimumWidth(110)

        input_layout.addWidget(self.mode_dropdown)

        # Voice/action button
        self.mic_btn = QPushButton("◉")

        self.mic_btn.setObjectName("composerIconButton")

        self.mic_btn.setToolTip("Voice input")

        self.mic_btn.setFixedSize(
            34,
            34,
        )

        input_layout.addWidget(self.mic_btn)

        # Send
        self.send_btn = QPushButton("↑")

        self.send_btn.setObjectName("sendButton")

        self.send_btn.setToolTip("Send")

        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.send_btn.setFixedSize(
            36,
            36,
        )

        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.send_btn)

        outer_layout.addWidget(input_card)

        # Composer hint
        hint_layout = QHBoxLayout()

        hint_layout.setContentsMargins(
            4,
            0,
            4,
            0,
        )

        hint = QLabel("Agent actions may require your approval")

        hint.setObjectName("composerHint")

        hint_layout.addWidget(hint)

        hint_layout.addStretch()

        shortcut = QLabel("Enter to send")

        shortcut.setObjectName("composerShortcut")

        hint_layout.addWidget(shortcut)

        outer_layout.addLayout(hint_layout)

        return outer

    # ========================================================================
    # Styling
    # ========================================================================

    def _apply_styles(self):
        """
        Apply the complete visual theme.

        Kept local to this widget so the chat UI can evolve independently
        from the rest of the application.
        """

        self.setStyleSheet("""
            /* ==========================================================
               Main container
               ========================================================== */

            QFrame#chatWindow {
                background: #f7f8fa;
                border: none;
            }

            /* ==========================================================
               Header
               ========================================================== */

            QFrame#chatHeader {
                background: #ffffff;
                border-bottom: 1px solid #e5e7eb;
            }

            QLabel#agentIcon {
                background: #111827;
                color: #ffffff;
                border-radius: 18px;
                font-size: 19px;
                font-weight: 700;
            }

            QLabel#agentTitle {
                color: #111827;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#agentStatus {
                color: #6b7280;
                font-size: 11px;
            }

            QLabel#statusIndicator {
                color: #22c55e;
                font-size: 10px;
                padding-right: 5px;
            }

            QPushButton#headerButton {
                background: #ffffff;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 11px;
                font-size: 11px;
            }

            QPushButton#headerButton:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
            }

            /* ==========================================================
               Chat display
               ========================================================== */

            QTextEdit#chatDisplay {
                background: #f7f8fa;
                color: #111827;
                border: none;
                padding: 18px;
                font-size: 13px;
                selection-background-color: #dbeafe;
                selection-color: #111827;
            }

            QTextEdit#chatDisplay QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 3px;
            }

            QTextEdit#chatDisplay QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 4px;
                min-height: 40px;
            }

            QTextEdit#chatDisplay QScrollBar::handle:vertical:hover {
                background: #9ca3af;
            }

            QTextEdit#chatDisplay QScrollBar::add-line:vertical,
            QTextEdit#chatDisplay QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QTextEdit#chatDisplay QScrollBar::add-page:vertical,
            QTextEdit#chatDisplay QScrollBar::sub-page:vertical {
                background: transparent;
            }

            /* ==========================================================
               Approval
               ========================================================== */

            QWidget#approvalContainer {
                background: #f7f8fa;
            }

            /* ==========================================================
               Composer
               ========================================================== */

            QFrame#composerOuter {
                background: #f7f8fa;
                border-top: 1px solid #e5e7eb;
            }

            QFrame#inputCard {
                background: #ffffff;
                border: 1px solid #dfe3e8;
                border-radius: 14px;
            }

            QFrame#inputCard:focus-within {
                border: 1px solid #9ca3af;
            }

            QLineEdit#messageInput {
                background: transparent;
                border: none;
                color: #111827;
                font-size: 13px;
                padding: 6px 4px;
                selection-background-color: #dbeafe;
            }

            QLineEdit#messageInput:disabled {
                color: #9ca3af;
            }

            QPushButton#composerIconButton {
                background: transparent;
                color: #6b7280;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
            }

            QPushButton#composerIconButton:hover {
                background: #f3f4f6;
                color: #111827;
            }

            QPushButton#composerIconButton:pressed {
                background: #e5e7eb;
            }

            QComboBox#modeDropdown {
                background: #f8fafc;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 600;
            }

            QComboBox#modeDropdown:hover {
                border-color: #d1d5db;
                background: #ffffff;
            }

            QComboBox#modeDropdown::drop-down {
                border: none;
                width: 22px;
            }

            QComboBox#modeDropdown QAbstractItemView {
                background: #ffffff;
                color: #111827;
                border: 1px solid #e5e7eb;
                selection-background-color: #f3f4f6;
                selection-color: #111827;
                padding: 4px;
            }

            QPushButton#sendButton {
                background: #111827;
                color: #ffffff;
                border: none;
                border-radius: 18px;
                font-size: 19px;
                font-weight: 700;
            }

            QPushButton#sendButton:hover {
                background: #1f2937;
            }

            QPushButton#sendButton:pressed {
                background: #374151;
            }

            QPushButton#sendButton:disabled {
                background: #d1d5db;
                color: #f9fafb;
            }

            QLabel#composerHint {
                color: #9ca3af;
                font-size: 10px;
            }

            QLabel#composerShortcut {
                color: #9ca3af;
                font-size: 10px;
            }
            """)

    # ========================================================================
    # Messaging
    # ========================================================================

    def send_message(self):
        """
        Send the current user message to Gemini.
        """

        user_text = self.input_field.text().strip()

        if not user_text:
            return

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            err_html = ChatMessageFormatter.format_message(
                "error",
                "GEMINI_API_KEY environment variable is not set!",
            )

            self.chat_display.append(err_html)

            return

        # --------------------------------------------------------------
        # Display user message
        # --------------------------------------------------------------

        user_html = ChatMessageFormatter.format_message(
            "user",
            user_text,
        )

        self.chat_display.append(user_html)

        self.input_field.clear()

        self._set_busy_state(True)

        self.current_response_text = ""
        self.is_first_chunk = True

        self._set_agent_status("Thinking...")

        # --------------------------------------------------------------
        # Worker
        # --------------------------------------------------------------

        self.worker = GeminiWorker(
            user_text,
            api_key,
        )

        self.worker.chat_chunk.connect(self.on_chat_chunk)

        self.worker.chat_finished.connect(self.on_chat_finished)

        self.worker.task_response.connect(self.on_task_response)

        self.worker.error_occurred.connect(self.on_error)

        self.worker.start()

    # ========================================================================
    # Streaming response
    # ========================================================================

    def on_chat_chunk(
        self,
        chunk_text: str,
    ):
        """
        Append streaming Gemini response.
        """

        self.current_response_text += chunk_text

        formatted_html = ChatMessageFormatter.format_message(
            "assistant",
            self.current_response_text,
        )

        if self.is_first_chunk:
            self.chat_display.append(formatted_html)

            self.is_first_chunk = False

        else:
            cursor = self.chat_display.textCursor()

            cursor.movePosition(QTextCursor.MoveOperation.End)

            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)

            cursor.removeSelectedText()

            cursor.insertHtml(formatted_html)

        self._scroll_to_bottom()

    # ========================================================================
    # Chat finished
    # ========================================================================

    def on_chat_finished(self):
        """
        Gemini completed a normal chat response.
        """

        self._set_agent_status("Ready")

        self._set_busy_state(False)

    # ========================================================================
    # Browser task detected
    # ========================================================================

    def on_task_response(
        self,
        intent: str,
        task_desc: str,
    ):
        intent_labels = {
            "BROWSER_TASK": "Browser Agent",
            "FILESYSTEM_TASK": "Filesystem Agent",
        }

        agent_label = intent_labels.get(
            intent,
            intent,
        )

        sys_html = ChatMessageFormatter.format_message(
            "system",
            (
                f"Intent classified as **{intent}**.\n"
                f"Dispatching task to **{agent_label}**:\n"
                f"`{task_desc}`"
            ),
        )

        self.chat_display.append(sys_html)
        self._set_agent_status("Preparing task...")

        self.task_created_signal.emit(
            intent,
            task_desc,
        )

        self._reset_input_state()

    # ========================================================================
    # Error
    # ========================================================================

    def on_error(
        self,
        error_msg: str,
    ):
        """
        Display worker errors.
        """

        err_html = ChatMessageFormatter.format_message(
            "error",
            error_msg,
        )

        self.chat_display.append(err_html)

        self._set_agent_status("Ready")

        self._reset_input_state()

    # ========================================================================
    # Busy state
    # ========================================================================

    def _set_busy_state(
        self,
        busy: bool,
    ):
        """
        Enable/disable composer controls.
        """

        self.input_field.setEnabled(not busy)

        self.send_btn.setEnabled(not busy)

        self.add_btn.setEnabled(not busy)

        self.mode_dropdown.setEnabled(not busy)

        self.mic_btn.setEnabled(not busy)

        if not busy:
            self.input_field.setFocus()

    def _reset_input_state(self):
        """
        Restore composer after task/chat processing.
        """

        self._set_busy_state(False)

        self._set_agent_status("Ready")

    # ========================================================================
    # Agent status
    # ========================================================================

    def _set_agent_status(
        self,
        status: str,
    ):
        """
        Update header status.
        """

        self.agent_status.setText(status)

        if status == "Ready":
            self.status_indicator.setText("●")
        else:
            self.status_indicator.setText("●")

    # ========================================================================
    # Approval UI
    # ========================================================================

    def show_approval_request(
        self,
        decision: ApprovalDecision,
    ):
        """
        Display the human approval UI for a REVIEW decision.

        This method intentionally remains compatible with MainWindow.
        """

        self.clear_approval_request()

        approval_widget = ApprovalWidget(
            decision,
            parent=self.approval_container,
        )

        approval_widget.approved.connect(self._on_approval_approved)

        approval_widget.denied.connect(self._on_approval_denied)

        self.approval_layout.addWidget(approval_widget)

        self.current_approval_widget = approval_widget

        self.approval_container.setVisible(True)

        self._set_agent_status("Waiting for approval")

        # Prevent another task while authorization is pending.
        self._set_busy_state(True)

        self._scroll_to_bottom()

    # ========================================================================
    # Clear approval
    # ========================================================================

    def clear_approval_request(self):
        """
        Remove the current approval UI.
        """

        while self.approval_layout.count():

            item = self.approval_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.current_approval_widget = None

        self.approval_container.setVisible(False)

    # ========================================================================
    # Approval granted
    # ========================================================================

    def _on_approval_approved(self):
        """
        Forward approval to MainWindow.
        """

        self.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                ("✅ Approval granted. " "Continuing with task execution..."),
            )
        )

        self.clear_approval_request()

        self._set_agent_status("Executing task...")

        self.approval_granted.emit()

    # ========================================================================
    # Approval denied
    # ========================================================================

    def _on_approval_denied(self):
        """
        Forward denial to MainWindow.
        """

        self.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                ("🛑 Task denied. " "Browser execution cancelled."),
            )
        )

        self.clear_approval_request()

        self._set_agent_status("Ready")

        self._set_busy_state(False)

        self.approval_denied.emit()

    # ========================================================================
    # Conversation helpers
    # ========================================================================

    def clear_conversation(self):
        """
        Start a clean visual conversation.

        This clears only the displayed conversation.
        It does not modify browser state or application state.
        """

        self.chat_display.clear()

        self.current_response_text = ""

        self.is_first_chunk = True

        self.clear_approval_request()

        self._set_agent_status("Ready")

        self._set_busy_state(False)

    def _scroll_to_bottom(self):
        """
        Keep the newest message visible.
        """

        scrollbar = self.chat_display.verticalScrollBar()

        scrollbar.setValue(scrollbar.maximum())
