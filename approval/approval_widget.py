from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .models import ApprovalDecision


class ApprovalWidget(QFrame):
    """
    Human approval UI for a task that has been classified as REVIEW.

    This widget does not execute the task.
    It only reports the user's decision through signals.
    """

    approved = Signal()
    denied = Signal()

    def __init__(
        self,
        decision: ApprovalDecision,
        parent=None,
    ):
        super().__init__(parent)

        self.decision = decision

        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)

        self.setStyleSheet("""
            QFrame {
                background-color: #f7f7f7;
                border: 1px solid #bdbdbd;
                border-radius: 8px;
            }

            QLabel#title {
                font-size: 15px;
                font-weight: bold;
                color: #111111;
                border: none;
            }

            QLabel#task_label {
                font-size: 13px;
                color: #222222;
                border: none;
            }

            QLabel#details {
                font-size: 12px;
                color: #555555;
                border: none;
            }

            QPushButton {
                min-height: 32px;
                padding: 4px 16px;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton#deny_button {
                background-color: white;
                color: #111111;
                border: 1px solid #999999;
            }

            QPushButton#deny_button:hover {
                background-color: #eeeeee;
            }

            QPushButton#approve_button {
                background-color: black;
                color: white;
                border: 1px solid black;
            }

            QPushButton#approve_button:hover {
                background-color: #333333;
            }
            """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel("🔐 Human approval required")
        title.setObjectName("title")

        layout.addWidget(title)

        classification = self.decision.classification

        operation = QLabel(f"<b>Operation:</b> {classification.operation_type}")
        operation.setObjectName("details")

        sensitivity = QLabel(
            f"<b>Data sensitivity:</b> " f"{classification.data_sensitivity}"
        )
        sensitivity.setObjectName("details")

        side_effect = QLabel(
            f"<b>External side effect:</b> " f"{classification.external_side_effect}"
        )
        side_effect.setObjectName("details")

        credential_use = QLabel(
            f"<b>Credential use:</b> " f"{classification.credential_use}"
        )
        credential_use.setObjectName("details")

        layout.addWidget(operation)
        layout.addWidget(sensitivity)
        layout.addWidget(side_effect)
        layout.addWidget(credential_use)

        reason_title = QLabel("<b>Why approval is required:</b>")
        reason_title.setObjectName("details")
        layout.addWidget(reason_title)

        for reason in self.decision.reasons:
            reason_label = QLabel(f"• {reason}")
            reason_label.setObjectName("details")
            reason_label.setWordWrap(True)
            layout.addWidget(reason_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.deny_button = QPushButton("Deny")
        self.deny_button.setObjectName("deny_button")

        self.approve_button = QPushButton("Approve & Continue")
        self.approve_button.setObjectName("approve_button")

        self.deny_button.clicked.connect(self._handle_denied)
        self.approve_button.clicked.connect(self._handle_approved)

        button_layout.addStretch()
        button_layout.addWidget(self.deny_button)
        button_layout.addWidget(self.approve_button)

        layout.addLayout(button_layout)

    def _handle_approved(self):
        self.approve_button.setEnabled(False)
        self.deny_button.setEnabled(False)
        self.approved.emit()

    def _handle_denied(self):
        self.approve_button.setEnabled(False)
        self.deny_button.setEnabled(False)
        self.denied.emit()
