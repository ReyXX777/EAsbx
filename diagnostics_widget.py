

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DiagnosticsWidget(QWidget):
    """Embedded agent diagnostics page.

    This widget owns only the presentation of agent diagnostics.
    MainWindow supplies the current agent status.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("DiagnosticsWidget")

        self._build_ui()





    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        root.setSpacing(12)

        title = QLabel("Agent Diagnostics")
        title.setObjectName("DiagnosticsTitle")
        title.setProperty("role", "title")

        subtitle = QLabel("Live status information for the active agent.")
        subtitle.setObjectName("DiagnosticsSubtitle")
        subtitle.setProperty("role", "muted")

        root.addWidget(title)
        root.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("DiagnosticsCard")
        card.setProperty("role", "panel")

        layout = QGridLayout(card)

        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)

        self.status_value = QLabel("Idle")
        self.steps_value = QLabel("0")
        self.action_value = QLabel("No agent running")
        self.error_value = QLabel("None")

        labels = (
            ("Agent Status", self.status_value),
            ("Steps Executed", self.steps_value),
            ("Last Action", self.action_value),
            ("Error", self.error_value),
        )

        for row, (label_text, value_label) in enumerate(labels):
            label = QLabel(label_text)
            label.setProperty("role", "muted")

            value_label.setProperty("role", "title")

            layout.addWidget(
                label,
                row,
                0,
            )

            layout.addWidget(
                value_label,
                row,
                1,
            )

        root.addWidget(card)
        root.addStretch()





    def refresh(self, status_info: dict) -> None:
        """Refresh the displayed diagnostics."""

        status = status_info.get(
            "status",
            "unknown",
        )

        steps = status_info.get(
            "current_step",
            0,
        )

        action = status_info.get(
            "last_action",
            "N/A",
        )

        error = status_info.get(
            "error",
            None,
        )

        self.status_value.setText(str(status).upper())

        self.steps_value.setText(str(steps))

        self.action_value.setText(str(action))

        self.error_value.setText(str(error) if error else "None")
