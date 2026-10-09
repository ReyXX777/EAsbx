from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QRadialGradient,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from qt_theme import ThemeManager


class MoonActivity(QWidget):
    """Animated moon-phase indicator for indeterminate processing.

    The widget is intentionally independent of any agent, task,
    observation, or application workflow.

    It represents activity rather than percentage progress.

    Animation sequence:

        New
        Crescent
        Half
        Gibbous
        Full
        Gibbous
        Half
        Crescent
        New
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
        )

        self.setMinimumSize(
            32,
            32,
        )

        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        self._phase = 0.0

        self._timer = QTimer(
            self,
        )

        self._timer.setInterval(
            45,
        )

        self._timer.timeout.connect(
            self._advance,
        )

        self._timer.start()





    def _advance(self) -> None:
        self._phase += 0.018

        if self._phase >= math.tau:
            self._phase -= math.tau

        self.update()





    def _theme_palette(self):
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
                QPainter.Antialiasing,
                True,
            )

            palette = self._theme_palette()

            size = min(
                self.width(),
                self.height(),
            )

            radius = size * 0.38

            center = QPointF(
                self.width() / 2.0,
                self.height() / 2.0,
            )





            moon_rect = (
                center.x() - radius,
                center.y() - radius,
                radius * 2.0,
                radius * 2.0,
            )





            dark_color = QColor(
                palette.surface,
            )

            dark_color = dark_color.darker(
                125,
            )

            painter.setPen(
                Qt.NoPen,
            )

            painter.setBrush(
                dark_color,
            )

            painter.drawEllipse(
                *moon_rect,
            )





            light_color = QColor(
                palette.accent,
            )

            light_color.setAlpha(
                235,
            )











            cosine = math.cos(
                self._phase,
            )

            ellipse_width = (
                abs(
                    cosine,
                )
                * radius
            )

            path = QPainterPath()

            if math.isclose(
                ellipse_width,
                0.0,
                abs_tol=0.001,
            ):

                if self._phase < math.pi:
                    path.moveTo(
                        center,
                    )

                    path.arcTo(
                        *moon_rect,
                        90,
                        180,
                    )

                    path.closeSubpath()

                else:
                    path.moveTo(
                        center,
                    )

                    path.arcTo(
                        *moon_rect,
                        -90,
                        180,
                    )

                    path.closeSubpath()

            elif cosine < 0:


                left = center.x() - ellipse_width

                path.moveTo(
                    center.x(),
                    center.y() - radius,
                )

                path.arcTo(
                    *moon_rect,
                    90,
                    180,
                )

                path.arcTo(
                    left,
                    center.y() - radius,
                    ellipse_width * 2.0,
                    radius * 2.0,
                    -90,
                    -180,
                )

                path.closeSubpath()

            else:


                right = center.x() - ellipse_width

                path.moveTo(
                    center.x(),
                    center.y() - radius,
                )

                path.arcTo(
                    *moon_rect,
                    90,
                    -180,
                )

                path.arcTo(
                    right,
                    center.y() - radius,
                    ellipse_width * 2.0,
                    radius * 2.0,
                    -90,
                    180,
                )

                path.closeSubpath()

            painter.setBrush(
                light_color,
            )

            painter.drawPath(
                path,
            )





            highlight = QRadialGradient(
                center.x() - radius * 0.25,
                center.y() - radius * 0.30,
                radius * 1.2,
            )

            highlight.setColorAt(
                0.0,
                QColor(
                    255,
                    255,
                    255,
                    35,
                ),
            )

            highlight.setColorAt(
                1.0,
                QColor(
                    255,
                    255,
                    255,
                    0,
                ),
            )

            painter.setBrush(
                highlight,
            )

            painter.drawEllipse(
                *moon_rect,
            )

        finally:
            painter.end()





    def stop(self) -> None:
        """Stop the animation."""

        self._timer.stop()

    def start(self) -> None:
        """Start the animation."""

        if not self._timer.isActive():
            self._timer.start()

    def closeEvent(
        self,
        event,
    ) -> None:
        self._timer.stop()

        super().closeEvent(
            event,
        )
