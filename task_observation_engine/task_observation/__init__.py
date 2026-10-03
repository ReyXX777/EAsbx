"""Standalone Stage 6 task observation and trace collection package."""

from .adapter import MathematicalApprovalAdapter
from .buckets import BucketManager
from .collectors import (
    ContinuousFeatureCollector,
    DiscreteFeatureCollector,
    EventTraceCollector,
)
from .models import (
    BucketKey,
    ContinuousObservation,
    DiscreteObservation,
    ObservationBucket,
    ObservationKind,
    ObservationSnapshot,
    TaskEvent,
    TaskIdentity,
    TracePoint,
)
from .replay import ReplayAPI
from .session import TaskObservationEngine, TaskObservationSession
from .simulation import generate_runs
from .session_store import SessionStore
from .qt import (
    ObservationBridge,
    ObservationPlot,
    ObservationWorker,
    ObservationWidget,
)

__all__ = [
    "MathematicalApprovalAdapter",
    "BucketManager",
    "ContinuousFeatureCollector",
    "DiscreteFeatureCollector",
    "EventTraceCollector",
    "BucketKey",
    "ContinuousObservation",
    "DiscreteObservation",
    "ObservationBucket",
    "ObservationKind",
    "ObservationSnapshot",
    "TaskEvent",
    "TaskIdentity",
    "TracePoint",
    "ReplayAPI",
    "TaskObservationEngine",
    "TaskObservationSession",
    "generate_runs",
    "SessionStore",
    "ObservationBridge",
    "ObservationPlot",
    "ObservationWorker",
    "ObservationWidget",
]
