from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..models import ObservationSnapshot
from .observation_plot import ObservationPlot


class ObservationContinuous(QWidget):
    """Continuous observation display."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__()

        self._snapshot: ObservationSnapshot | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        group = QGroupBox(
            "③ CONTINUOUS OBSERVATIONS",
        )

        group_layout = QVBoxLayout(
            group,
        )

        selector_layout = QHBoxLayout()

        selector_layout.addWidget(
            QLabel("Feature:"),
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

    def set_snapshot(
        self,
        snapshot: ObservationSnapshot | None,
    ) -> None:
        self._snapshot = snapshot

        self.feature_selector.blockSignals(
            True,
        )

        try:
            self.feature_selector.clear()

            if snapshot is not None:
                names = []

                for observation in snapshot.continuous:
                    name = str(
                        observation.name,
                    )

                    if name and name not in names:
                        names.append(name)

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

    def _render_selected(
        self,
        name: str,
    ) -> None:
        snapshot = self._snapshot

        if snapshot is None or not name:
            self.plot.clear()
            return

        values = []

        for observation in snapshot.continuous:
            if observation.name != name:
                continue

            if observation.value is None:
                continue

            try:
                values.append(
                    float(observation.value),
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        self.plot.set_data(
            values,
            name,
        )

    def clear(self) -> None:
        self._snapshot = None
        self.feature_selector.clear()
        self.plot.clear()
