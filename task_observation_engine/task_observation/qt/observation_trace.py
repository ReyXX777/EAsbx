from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import TracePoint


class ObservationTrace(QWidget):
    """Detailed inspector for a selected trace point."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__()

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        group = QGroupBox(
            "④ TRACE INSPECTOR",
        )

        group_layout = QVBoxLayout(
            group,
        )

        form = QFormLayout()

        self.phase_label = QLabel("—")
        self.action_label = QLabel("—")
        self.path_label = QLabel("—")
        self.timestamp_label = QLabel("—")
        self.sequence_label = QLabel("—")

        form.addRow(
            "Phase:",
            self.phase_label,
        )

        form.addRow(
            "Action:",
            self.action_label,
        )

        form.addRow(
            "Path:",
            self.path_label,
        )

        form.addRow(
            "Timestamp:",
            self.timestamp_label,
        )

        form.addRow(
            "Sequence:",
            self.sequence_label,
        )

        group_layout.addLayout(
            form,
        )

        group_layout.addWidget(
            QLabel("Values:"),
        )

        self.values_edit = QPlainTextEdit()

        self.values_edit.setReadOnly(
            True,
        )

        group_layout.addWidget(
            self.values_edit,
            1,
        )

        layout.addWidget(
            group,
        )

    def set_trace(
        self,
        trace: TracePoint | None,
    ) -> None:
        if trace is None:
            self.clear()
            return

        self.phase_label.setText(
            self._safe_text(
                trace.phase,
            )
        )

        self.action_label.setText(
            self._safe_text(
                trace.action,
            )
        )

        self.path_label.setText(
            self._safe_text(
                trace.path,
            )
        )

        self.timestamp_label.setText(
            self._safe_text(
                trace.timestamp,
            )
        )

        self.sequence_label.setText(
            self._safe_text(
                trace.sequence,
            )
        )

        values = {
            "discrete": dict(
                trace.discrete,
            ),
            "continuous": dict(
                trace.continuous,
            ),
        }

        self.values_edit.setPlainText(
            repr(values),
        )

    def clear(self) -> None:
        self.phase_label.setText("—")
        self.action_label.setText("—")
        self.path_label.setText("—")
        self.timestamp_label.setText("—")
        self.sequence_label.setText("—")
        self.values_edit.clear()

    @staticmethod
    def _safe_text(
        value: Any,
    ) -> str:
        if value is None:
            return "<missing>"

        try:
            return str(value)

        except Exception:
            return "<unprintable>"
