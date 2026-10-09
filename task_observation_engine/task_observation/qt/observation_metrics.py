from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QSizePolicy,
    QWidget,
)

from ..models import ObservationSnapshot


class ObservationMetrics(QWidget):
    """Derived task metrics dashboard.

    Visual styling is delegated to the global MOCKAPP Qt theme.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
        )

        self.setProperty(
            "role",
            "panel",
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self._build_ui()





    def _build_ui(self) -> None:
        layout = QGridLayout(
            self,
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            0,
        )

        group = QGroupBox(
            "② METRICS DASHBOARD",
        )

        group.setProperty(
            "role",
            "panel",
        )

        group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        grid = QGridLayout(
            group,
        )

        grid.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        grid.setHorizontalSpacing(
            12,
        )

        grid.setVerticalSpacing(
            8,
        )

        self.events_value = self._metric(
            grid,
            0,
            "Events",
        )

        self.tools_value = self._metric(
            grid,
            1,
            "Tool Calls",
        )

        self.files_value = self._metric(
            grid,
            2,
            "File Accesses",
        )

        self.duration_value = self._metric(
            grid,
            3,
            "Duration",
        )



        grid.setColumnStretch(
            0,
            0,
        )

        grid.setColumnStretch(
            1,
            1,
        )



        for row in range(4):
            grid.setRowStretch(
                row,
                1,
            )

        layout.addWidget(
            group,
            0,
            0,
        )

        layout.setRowStretch(
            0,
            1,
        )

        layout.setColumnStretch(
            0,
            1,
        )





    @staticmethod
    def _metric(
        layout: QGridLayout,
        row: int,
        label: str,
    ) -> QLabel:
        name = QLabel(
            label,
        )

        name.setProperty(
            "role",
            "muted",
        )

        name.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Preferred,
        )

        value = QLabel(
            "—",
        )

        value.setProperty(
            "role",
            "value",
        )

        value.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter,
        )

        value.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout.addWidget(
            name,
            row,
            0,
        )

        layout.addWidget(
            value,
            row,
            1,
        )

        return value





    def set_snapshot(
        self,
        snapshot: ObservationSnapshot | None,
    ) -> None:
        if snapshot is None:
            self.clear()
            return

        continuous = {item.name: item.value for item in snapshot.continuous}

        event_count = len(
            snapshot.events,
        )

        total_tool_calls = self._first_value(
            continuous,
            "total_tool_calls",
        )

        file_accesses = self._first_value(
            continuous,
            "file_access_count",
        )

        duration = self._first_value(
            continuous,
            "task_duration_seconds",
        )

        self.events_value.setText(
            str(event_count),
        )

        self.tools_value.setText(
            self._format_number(
                total_tool_calls,
            )
        )

        self.files_value.setText(
            self._format_number(
                file_accesses,
            )
        )

        self.duration_value.setText(
            self._format_duration(
                duration,
            )
        )





    @staticmethod
    def _first_value(
        values: dict[str, Any],
        name: str,
    ) -> Any:
        return values.get(
            name,
        )

    @staticmethod
    def _format_number(
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            numeric = float(
                value,
            )

            if numeric.is_integer():
                return str(
                    int(numeric),
                )

            return f"{numeric:.2f}"

        except (
            TypeError,
            ValueError,
        ):
            return str(value)

    @staticmethod
    def _format_duration(
        value: Any,
    ) -> str:
        if value is None:
            return "—"

        try:
            seconds = int(
                float(value),
            )

        except (
            TypeError,
            ValueError,
        ):
            return str(value)

        minutes, seconds = divmod(
            seconds,
            60,
        )

        return f"{minutes:02d}:{seconds:02d}"





    def clear(self) -> None:
        self.events_value.setText(
            "—",
        )

        self.tools_value.setText(
            "—",
        )

        self.files_value.setText(
            "—",
        )

        self.duration_value.setText(
            "—",
        )
