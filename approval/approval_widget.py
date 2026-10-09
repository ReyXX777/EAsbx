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


        self.setProperty("role", "panel")

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel("Human approval required")
        title.setObjectName("title")
        title.setProperty("role", "title")

        layout.addWidget(title)

        classification = self.decision.classification

        operation = QLabel(f"<b>Operation:</b> {classification.operation_type}")
        operation.setObjectName("details")
        operation.setProperty("role", "muted")

        sensitivity = QLabel(
            f"<b>Data sensitivity:</b> {classification.data_sensitivity}"
        )
        sensitivity.setObjectName("details")
        sensitivity.setProperty("role", "muted")

        side_effect = QLabel(
            f"<b>External side effect:</b> " f"{classification.external_side_effect}"
        )
        side_effect.setObjectName("details")
        side_effect.setProperty("role", "muted")

        credential_use = QLabel(
            f"<b>Credential use:</b> {classification.credential_use}"
        )
        credential_use.setObjectName("details")
        credential_use.setProperty("role", "muted")

        layout.addWidget(operation)
        layout.addWidget(sensitivity)
        layout.addWidget(side_effect)
        layout.addWidget(credential_use)

        reason_title = QLabel("<b>Why approval is required:</b>")
        reason_title.setObjectName("details")
        reason_title.setProperty("role", "muted")
        layout.addWidget(reason_title)

        for reason in self.decision.reasons:
            reason_label = QLabel(f"• {reason}")
            reason_label.setObjectName("details")
            reason_label.setProperty("role", "muted")
            reason_label.setWordWrap(True)
            layout.addWidget(reason_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.deny_button = QPushButton("Deny")
        self.deny_button.setObjectName("deny_button")
        self.deny_button.setProperty("role", "secondary_action")

        self.approve_button = QPushButton("Approve & Continue")
        self.approve_button.setObjectName("approve_button")
        self.approve_button.setProperty("role", "primary_action")

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
