from __future__ import annotations

import os
from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication

from task_observation.qt import (
    ObservationPlot,
    ObservationWidget,
)


@pytest.fixture(scope="session")
def qapp():
    os.environ.setdefault(
        "QT_QPA_PLATFORM",
        "offscreen",
    )

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def test_observation_plot_can_receive_values(
    qapp,
):
    plot = ObservationPlot()

    plot.set_data(
        [
            1.0,
            2.0,
            3.0,
            5.0,
        ],
        "row_count",
    )

    assert plot._values == [
        1.0,
        2.0,
        3.0,
        5.0,
    ]


def test_observation_widget_can_be_created(
    qapp,
    tmp_path: Path,
):
    widget = ObservationWidget(
        tmp_path,
    )

    assert widget.bridge is not None
    assert widget.plot is not None
    assert widget.history_list is not None

    widget.bridge.close()
