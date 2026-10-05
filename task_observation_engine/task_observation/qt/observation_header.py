from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class ObservationHeader(QWidget):
    """Header for the Observation Monitor."""

    refresh_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.title_label = QLabel(
            "OBSERVATION MONITOR",
        )

        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        layout.addWidget(
            self.title_label,
        )

        layout.addStretch()

        self.live_label = QLabel(
            "🔴 Live",
        )

        self.live_label.setProperty(
            "role",
            "status_indicator",
        )

        self.live_label.setProperty(
            "status",
            "live",
        )

        layout.addWidget(
            self.live_label,
        )

        self.refresh_button = QPushButton(
            "⟳ Refresh",
        )

        self.refresh_button.clicked.connect(
            self.refresh_requested,
        )

        layout.addWidget(
            self.refresh_button,
        )

    def set_live(
        self,
        live: bool,
    ) -> None:
        if live:
            self.live_label.setText(
                "● LIVE",
            )
        else:
            self.live_label.setText(
                "● IDLE",
            )
