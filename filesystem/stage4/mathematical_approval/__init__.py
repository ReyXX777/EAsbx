"""Standalone mathematical approval package.

Stage 1 intentionally has no dependency on MOCKAPP filesystem/browser code.
"""

from .models import (
    ActionObservation,
    DecisionLabel,
    FeatureVector,
    TaskFamily,
    TaskHistory,
)
from .probability import PMFModel, PDFModel
from .geometry import JacobianModel, HessianModel
from .decision import ApprovalDecision, MathematicalApprovalEngine

__all__ = [
    "ActionObservation",
    "DecisionLabel",
    "FeatureVector",
    "TaskFamily",
    "TaskHistory",
    "PMFModel",
    "PDFModel",
    "JacobianModel",
    "HessianModel",
    "ApprovalDecision",
    "MathematicalApprovalEngine",
]
from .history import LabeledObservation, LabeledTaskHistory
from .stage4 import HistoryAwareApprovalEngine, Stage4Decision, Stage4HistoryHarness, Stage4Metrics, Stage4Report
