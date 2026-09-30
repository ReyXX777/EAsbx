import json
import os
from google import genai
from google.genai import types
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chat_formatter import ChatMessageFormatter
from PySide6.QtGui import QTextCursor
from approval.approval_widget import ApprovalWidget
from approval.models import ApprovalDecision


class GeminiWorker(QThread):
    chat_chunk = Signal(str)
    chat_finished = Signal()
    task_response = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, prompt, api_key, chat_session=None):
        super().__init__()
        self.prompt = prompt
        self.api_key = api_key
        self.chat_session = chat_session

    def run(self):
        try:
            client = genai.Client(api_key=self.api_key)

            # System instruction enforcing JSON intent classification
            system_instruction = (
                "You are an intent classification system for an AI assistant. "
                "Classify the user prompt as either 'BROWSER_TASK' or 'CHAT'.\n"
                "- Use 'BROWSER_TASK' if the prompt involves web navigation, searching online, clicking, scraping, opening URLs, or interacting with web applications.\n"
                "- Use 'CHAT' if the user is asking general questions, chatting, coding, or summarizing without needing live web actions.\n"
                "Return JSON matching the schema."
            )

            # Load JSON schema structure
            schema_path = os.path.join(os.path.dirname(__file__), "intent_schema.json")
            response_schema = None
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    response_schema = json.load(f)

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            )

            # Fast single turn call to classify intent
            classification_prompt = f"Analyze intent for: '{self.prompt}'"
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=classification_prompt,
                config=config,
            )

            data = json.loads(response.text)
            intent = data.get("intent", "CHAT")
            task_desc = data.get("task_description", self.prompt)

            if intent == "BROWSER_TASK":
                self.task_response.emit(task_desc)
            else:
                # Handle general chat session with streaming
                if self.chat_session is None:
                    chat = client.chats.create(model="gemini-3.5-flash-lite")
                else:
                    chat = self.chat_session

                response_stream = chat.send_message_stream(self.prompt)
                for chunk in response_stream:
                    if chunk.text:
                        self.chat_chunk.emit(chunk.text)
                self.chat_finished.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatWindowWidget(QFrame):
    task_created_signal = Signal(str)
    approval_granted = Signal()
    approval_denied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("border: none; font-size: 14px;")
        main_layout.addWidget(self.chat_display, stretch=1)

        self.approval_container = QWidget()
        self.approval_container.setVisible(False)

        self.approval_layout = QVBoxLayout(self.approval_container)

        self.approval_layout.setContentsMargins(0, 5, 0, 5)

        main_layout.addWidget(self.approval_container)
        self.current_approval_widget = None

        # Bottom Input Toolbar
        input_box = QFrame()
        input_box.setFrameShape(QFrame.Box)
        input_box.setFixedHeight(60)
        input_box.setStyleSheet("background-color: white;")

        input_layout = QHBoxLayout(input_box)
        input_layout.setContentsMargins(8, 5, 8, 5)
        input_layout.setSpacing(8)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(35, 35)
        self.add_btn.setStyleSheet("font-size: 20px; border: none; font-weight: bold;")

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Send Another Message...")
        self.input_field.setStyleSheet("border: none; font-size: 13px;")
        self.input_field.returnPressed.connect(self.send_message)

        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["Auto", "Manual", "Step-by-Step"])
        self.mode_dropdown.setStyleSheet("""
            QComboBox {
                border: 1px solid black;
                padding: 2px 8px;
                font-weight: bold;
                background-color: white;
            }
        """)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(35, 35)
        self.mic_btn.setStyleSheet("border: none; font-size: 16px;")

        self.send_btn = QPushButton("➔")
        self.send_btn.setFixedSize(35, 35)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border-radius: 17px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.add_btn)
        input_layout.addWidget(self.input_field, stretch=1)
        input_layout.addWidget(self.mode_dropdown)
        input_layout.addWidget(self.mic_btn)
        input_layout.addWidget(self.send_btn)

        main_layout.addWidget(input_box)

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            err_html = ChatMessageFormatter.format_message(
                "error", "GEMINI_API_KEY environment variable is not set!"
            )
            self.chat_display.append(err_html)
            return

        user_html = ChatMessageFormatter.format_message("user", user_text)
        self.chat_display.append(user_html)
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        self.current_response_text = ""
        self.is_first_chunk = True

        self.worker = GeminiWorker(user_text, api_key)
        self.worker.chat_chunk.connect(self.on_chat_chunk)
        self.worker.chat_finished.connect(self.on_chat_finished)
        self.worker.task_response.connect(self.on_task_response)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_chat_chunk(self, chunk_text: str):
        self.current_response_text += chunk_text
        formatted_html = ChatMessageFormatter.format_message(
            "assistant", self.current_response_text
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

    def on_chat_finished(self):
        self._reset_input_state()

    def on_task_response(self, task_desc):
        sys_html = ChatMessageFormatter.format_message(
            "system",
            f"Intent classified as **BROWSER_TASK**. Dispatching task to browser agent:\n`{task_desc}`",
        )
        self.chat_display.append(sys_html)
        self.task_created_signal.emit(task_desc)
        self._reset_input_state()

    def on_error(self, error_msg):
        err_html = ChatMessageFormatter.format_message("error", error_msg)
        self.chat_display.append(err_html)
        self._reset_input_state()

    def _reset_input_state(self):
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def show_approval_request(
        self,
        decision: ApprovalDecision,
    ):
        """
        Display the human approval UI for a REVIEW decision.
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

        # Prevent starting another task while approval is pending.
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

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

    def _on_approval_approved(self):
        """
        Forward the approval decision to MainWindow.
        """

        self.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "✅ Approval granted. Continuing with browser execution...",
            )
        )

        self.clear_approval_request()

        self.approval_granted.emit()

    def _on_approval_denied(self):
        """
        Forward the denial decision to MainWindow.
        """

        self.chat_display.append(
            ChatMessageFormatter.format_message(
                "system",
                "🛑 Task denied. Browser execution cancelled.",
            )
        )

        self.clear_approval_request()

        self.approval_denied.emit()
