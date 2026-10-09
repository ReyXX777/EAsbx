from __future__ import annotations

import math
from typing import Iterable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from qt_theme import ThemeManager


class ObservationPlot(QWidget):
    """Small dependency-free Qt plot for continuous observations.

    The plot is intentionally independent of:

    - TaskObservationSession
    - TaskObservationEngine
    - SessionStore
    - ReplayAPI
    - collector implementations

    It only receives numeric values and renders them.

    Visual styling is provided by the global MOCKAPP Qt theme.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
        )

        self.setMinimumHeight(
            220,
        )

        self._values: list[float] = []





    def set_data(
        self,
        values: Iterable[float],
    ) -> None:
        """Replace the plotted values."""

        cleaned: list[float] = []

        for value in values:
            try:
                numeric = float(value)

            except (
                TypeError,
                ValueError,
            ):
                continue

            if not math.isfinite(numeric):
                continue

            cleaned.append(
                numeric,
            )

        self._values = cleaned

        self.update()

    def clear(self) -> None:
        """Clear the current plot."""

        self._values.clear()

        self.update()





    def _theme_palette(self):
        """Return the current global theme palette."""

        return ThemeManager.instance().palette





    def paintEvent(
        self,
        _event,
    ) -> None:
        painter = QPainter(
            self,
        )

        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing,
                True,
            )

            palette = self._theme_palette()

            rect = self.rect().adjusted(
                45,
                25,
                -20,
                -35,
            )





            if not self._values:
                painter.setPen(
                    QColor(
                        palette.text_muted,
                    ),
                )

                painter.drawText(
                    rect,
                    Qt.AlignmentFlag.AlignCenter,
                    "No numeric observations.",
                )

                return





            minimum = min(
                self._values,
            )

            maximum = max(
                self._values,
            )

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





            frame_pen = QPen(
                QColor(
                    palette.border,
                ),
                1.0,
            )

            painter.setPen(
                frame_pen,
            )

            painter.setBrush(
                Qt.BrushStyle.NoBrush,
            )

            painter.drawRect(
                rect,
            )





            point_count = len(
                self._values,
            )

            points: list[QPointF] = []

            for index, value in enumerate(
                self._values,
            ):
                if point_count == 1:
                    x = float(
                        rect.center().x(),
                    )

                else:
                    x = rect.left() + (index / (point_count - 1)) * rect.width()

                normalized = (value - minimum) / (maximum - minimum)

                y = rect.bottom() - normalized * rect.height()

                points.append(
                    QPointF(
                        x,
                        y,
                    ),
                )





            line_pen = QPen(
                QColor(
                    palette.accent,
                ),
                2.0,
            )

            line_pen.setCapStyle(
                Qt.PenCapStyle.RoundCap,
            )

            line_pen.setJoinStyle(
                Qt.PenJoinStyle.RoundJoin,
            )

            painter.setPen(
                line_pen,
            )

            if len(points) >= 2:
                painter.drawPolyline(
                    points,
                )

            else:
                painter.setBrush(
                    QColor(
                        palette.accent,
                    ),
                )

                painter.drawEllipse(
                    points[0],
                    3.0,
                    3.0,
                )





            painter.setPen(
                QColor(
                    palette.text_muted,
                ),
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
