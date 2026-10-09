from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..history import ObservationHistory
from .observation_plot import ObservationPlot


class ObservationContinuous(QWidget):
    """Continuous observation display backed by aggregated history."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
        )

        self._history: ObservationHistory | None = None

        self._build_ui()





    def _build_ui(self) -> None:
        layout = QVBoxLayout(
            self,
        )

        group = QGroupBox(
            "③ CONTINUOUS OBSERVATIONS",
        )

        group_layout = QVBoxLayout(
            group,
        )

        selector_layout = QHBoxLayout()

        feature_label = QLabel(
            "Feature:",
        )

        feature_label.setProperty(
            "role",
            "muted",
        )

        selector_layout.addWidget(
            feature_label,
        )

        self.feature_selector = QComboBox()

        selector_layout.addWidget(
            self.feature_selector,
            1,
        )

        group_layout.addLayout(
            selector_layout,
        )

        self.plot = ObservationPlot()

        group_layout.addWidget(
            self.plot,
            1,
        )

        layout.addWidget(
            group,
        )

        self.feature_selector.currentTextChanged.connect(
            self._render_selected,
        )





    def set_history(
        self,
        history: ObservationHistory | None,
    ) -> None:
        """Attach the aggregated observation history to the widget."""

        self._history = history

        self._refresh_features()

    def _refresh_features(self) -> None:
        history = self._history

        self.feature_selector.blockSignals(
            True,
        )

        try:
            self.feature_selector.clear()

            if history is None:
                self.plot.clear()
                return

            try:
                names = [str(name) for name in history.feature_names() if str(name)]

            except Exception:
                names = []

            self.feature_selector.addItems(
                names,
            )

        finally:
            self.feature_selector.blockSignals(
                False,
            )

        self._render_selected(
            self.feature_selector.currentText(),
        )

    def refresh(self) -> None:
        """Refresh the feature list and plot from aggregated history."""

        history = self._history

        if history is None:
            self.feature_selector.clear()
            self.plot.clear()
            return

        try:
            history.refresh()

        except Exception:

            pass

        self._refresh_features()





    def _render_selected(
        self,
        name: str,
    ) -> None:
        history = self._history

        if history is None or not name:
            self.plot.clear()
            return

        try:
            raw_values = history.get_values(
                name,
            )

        except Exception:
            raw_values = []

        values = []

        for value in raw_values:
            if value is None:
                continue

            try:
                values.append(
                    float(value),
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

        if not values:
            self.plot.clear()
            return

        self.plot.set_data(
            values,
        )





    def clear(self) -> None:
        self._history = None

        self.feature_selector.clear()

        self.plot.clear()
