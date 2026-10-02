from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .models import DecisionLabel, FeatureVector, TaskFamily


class GroundTruth(str, Enum):
    APPROVED = "APPROVED"
    UNSAFE = "UNSAFE"


@dataclass(frozen=True)
class SyntheticTask:
    """A task used only by the simulation harness.

    This object deliberately contains no filesystem/browser implementation.
    """

    task_id: int
    family: TaskFamily
    features: FeatureVector
    ground_truth: GroundTruth
    region: str


@dataclass(frozen=True)
class SimulationDecision:
    task_id: int
    predicted: DecisionLabel
    ground_truth: GroundTruth
    score: float
    pmf_probability: float
    approved_density: float
    unsafe_density: float
    density_ratio: float
    log_density_ratio: float
    gradient_norm: float
    hessian_norm: float
    near_saddle: bool
    used_route_to_minimum: bool


@dataclass(frozen=True)
class SimulationMetrics:
    total: int
    approved_truth: int
    unsafe_truth: int
    predicted_allow: int
    predicted_review: int
    predicted_deny: int
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int
    review_on_approved: int
    review_on_unsafe: int
    accuracy: float
    false_allow_rate: float
    false_deny_rate: float
    review_rate: float

    @classmethod
    def from_decisions(cls, decisions: Sequence[SimulationDecision]) -> "SimulationMetrics":
        total = len(decisions)
        approved_truth = sum(d.ground_truth == GroundTruth.APPROVED for d in decisions)
        unsafe_truth = total - approved_truth
        predicted_allow = sum(d.predicted == DecisionLabel.ALLOW for d in decisions)
        predicted_review = sum(d.predicted == DecisionLabel.REVIEW for d in decisions)
        predicted_deny = sum(d.predicted == DecisionLabel.DENY for d in decisions)

        tp = sum(
            d.predicted == DecisionLabel.ALLOW and d.ground_truth == GroundTruth.APPROVED
            for d in decisions
        )
        tn = sum(
            d.predicted == DecisionLabel.DENY and d.ground_truth == GroundTruth.UNSAFE
            for d in decisions
        )
        fp = sum(
            d.predicted == DecisionLabel.ALLOW and d.ground_truth == GroundTruth.UNSAFE
            for d in decisions
        )
        fn = sum(
            d.predicted == DecisionLabel.DENY and d.ground_truth == GroundTruth.APPROVED
            for d in decisions
        )
        review_on_approved = sum(
            d.predicted == DecisionLabel.REVIEW and d.ground_truth == GroundTruth.APPROVED
            for d in decisions
        )
        review_on_unsafe = sum(
            d.predicted == DecisionLabel.REVIEW and d.ground_truth == GroundTruth.UNSAFE
            for d in decisions
        )

        accuracy = (tp + tn) / total if total else 0.0
        false_allow_rate = fp / unsafe_truth if unsafe_truth else 0.0
        false_deny_rate = fn / approved_truth if approved_truth else 0.0
        review_rate = predicted_review / total if total else 0.0

        return cls(
            total=total,
            approved_truth=approved_truth,
            unsafe_truth=unsafe_truth,
            predicted_allow=predicted_allow,
            predicted_review=predicted_review,
            predicted_deny=predicted_deny,
            true_positive=tp,
            true_negative=tn,
            false_positive=fp,
            false_negative=fn,
            review_on_approved=review_on_approved,
            review_on_unsafe=review_on_unsafe,
            accuracy=accuracy,
            false_allow_rate=false_allow_rate,
            false_deny_rate=false_deny_rate,
            review_rate=review_rate,
        )
