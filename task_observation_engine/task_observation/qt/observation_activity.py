from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import ObservationSnapshot, TracePoint


class ObservationActivity(QWidget):
    """Activity timeline for a task observation."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        group = QGroupBox(
            "① ACTIVITY TIMELINE",
        )

        group_layout = QVBoxLayout(
            group,
        )

        self.timeline = QListWidget()

        group_layout.addWidget(
            self.timeline,
        )

        layout.addWidget(
            group,
        )

    def set_snapshot(
        self,
        snapshot: ObservationSnapshot | None,
    ) -> None:
        self.timeline.clear()

        if snapshot is None:
            return

        for trace in snapshot.traces:
            if not isinstance(
                trace,
                TracePoint,
            ):
                continue

            if trace.phase == "task_started":
                prefix = "●"
            elif trace.phase == "tool_started":
                prefix = "●"
            elif trace.phase == "tool_completed":
                prefix = "✓"
            elif trace.phase == "tool_failed":
                prefix = "✕"
            else:
                prefix = "●"

            action = str(trace.action) if trace.action else trace.phase

            item = QListWidgetItem(f"{prefix} {action}")

            item.setData(
                256,
                trace,
            )

            self.timeline.addItem(
                item,
            )

        self._add_event_fallback(snapshot)

    def _add_event_fallback(
        self,
        snapshot: ObservationSnapshot,
    ) -> None:
        if snapshot.traces:
            return

        for event in snapshot.events:
            name = getattr(
                event,
                "name",
                "event",
            )

            self.timeline.addItem(
                f"● {name}",
            )

    def clear(self) -> None:
        self.timeline.clear()
