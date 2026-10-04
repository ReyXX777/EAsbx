from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from task_observation.qt.observation_plot import ObservationPlot


@pytest.fixture
def qt_app():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def test_plot_filters_invalid_numeric_values(
    qt_app,
) -> None:
    plot = ObservationPlot()

    plot.set_data(
        [
            1,
            "2.5",
            None,
            "bad",
            float("nan"),
            float("inf"),
            4,
        ],
        title="row_count",
    )

    assert plot._values == [
        1.0,
        2.5,
        4.0,
    ]

    assert plot._title == "row_count"


def test_plot_clear_removes_values(
    qt_app,
) -> None:
    plot = ObservationPlot()

    plot.set_data(
        [1, 2, 3],
    )

    assert plot._values == [
        1.0,
        2.0,
        3.0,
    ]

    plot.clear()

    assert plot._values == []
