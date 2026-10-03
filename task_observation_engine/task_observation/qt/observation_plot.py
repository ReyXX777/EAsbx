from __future__ import annotations

import math
from typing import Iterable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget


class ObservationPlot(QWidget):
    """Small dependency-free Qt plot for continuous observations.

    The plot is intentionally independent of:

    - TaskObservationSession
    - TaskObservationEngine
    - SessionStore
    - ReplayAPI
    - collector implementations

    It only receives numeric values and renders them.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setMinimumHeight(220)

        self._values: list[float] = []
        self._title = "Continuous Feature"

    def set_data(
        self,
        values: Iterable[float],
        title: str = "Continuous Feature",
    ) -> None:
        """Replace the plotted values."""

        cleaned: list[float] = []

        for value in values:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue

            if not math.isfinite(numeric):
                continue

            cleaned.append(numeric)

        self._values = cleaned
        self._title = str(title)

        self.update()

    def clear(self) -> None:
        """Clear the current plot."""

        self._values.clear()
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)

        try:
            painter.setRenderHint(
                QPainter.Antialiasing,
                True,
            )

            rect = self.rect().adjusted(
                45,
                25,
                -20,
                -35,
            )

            painter.drawText(
                10,
                18,
                self._title,
            )

            if not self._values:
                painter.drawText(
                    rect,
                    Qt.AlignCenter,
                    "No numeric observations.",
                )
                return

            minimum = min(self._values)
            maximum = max(self._values)

            if math.isclose(
                minimum,
                maximum,
            ):
                padding = max(
                    abs(minimum) * 0.05,
                    1.0,
                )

                minimum -= padding
                maximum += padding

            painter.drawRect(
                rect,
            )

            point_count = len(self._values)

            points: list[QPointF] = []

            for index, value in enumerate(self._values):
                if point_count == 1:
                    x = float(rect.center().x())
                else:
                    x = rect.left() + (index / (point_count - 1)) * rect.width()

                normalized = (value - minimum) / (maximum - minimum)

                y = rect.bottom() - normalized * rect.height()

                points.append(
                    QPointF(
                        x,
                        y,
                    )
                )

            if len(points) >= 2:
                painter.drawPolyline(
                    points,
                )
            else:
                painter.drawEllipse(
                    points[0],
                    3,
                    3,
                )

            painter.drawText(
                5,
                rect.top(),
                f"{maximum:.4g}",
            )

            painter.drawText(
                5,
                rect.bottom(),
                f"{minimum:.4g}",
            )

            painter.drawText(
                rect.left(),
                rect.bottom() + 25,
                "start",
            )

            painter.drawText(
                rect.right() - 35,
                rect.bottom() + 25,
                "end",
            )

        finally:
            painter.end()
