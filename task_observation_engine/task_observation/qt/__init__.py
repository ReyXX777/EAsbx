"""Qt presentation layer for the task observation engine.

The Qt layer is intentionally downstream of the observation engine.

Qt is responsible for:

- starting and finishing observation sessions through a bridge
- displaying live observation snapshots
- displaying persisted sessions through ReplayAPI
- visualizing continuous observations

Qt does not own observation-session state or storage state.
"""

from .observation_bridge import ObservationBridge
from .observation_plot import ObservationPlot
from .observation_thread import ObservationWorker
from .observation_widget import ObservationWidget

__all__ = [
    "ObservationBridge",
    "ObservationPlot",
    "ObservationWorker",
    "ObservationWidget",
]
