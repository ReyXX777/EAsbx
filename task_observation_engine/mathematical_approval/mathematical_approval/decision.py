from __future__ import annotations

import math
from typing import Callable, Optional

from .geometry import HessianModel, JacobianModel, build_geometry_estimate
from .models import (
    ActionObservation,
    ApprovalDecision,
    DecisionLabel,
    FeatureVector,
    TaskFamily,
    TaskHistory,
)
from .probability import PDFModel, PMFModel


class MathematicalApprovalEngine:
    """Standalone mathematical decision layer.

    Important design constraint:
    this class does not know what a filesystem task, browser task, or
    credential is. The caller supplies a family and numeric feature vector.

    The output is a decision signal. A future adapter may combine it with
    hard safety policy, deny-lists, permissions, or human review.
    """

    def __init__(
        self,
        pmf: Optional[PMFModel] = None,
        pdf: Optional[PDFModel] = None,
        jacobian: Optional[JacobianModel] = None,
        hessian: Optional[HessianModel] = None,
        allow_threshold: float = 0.95,
        deny_threshold: float = 0.20,
        min_samples_for_automatic: int = 10,
        saddle_margin: float = 0.10,
    ) -> None:
        if not 0.5 < allow_threshold < 1.0:
            raise ValueError("allow_threshold must be between 0.5 and 1.")
        if 0.0 < deny_threshold >= allow_threshold:
            raise ValueError("deny_threshold must be below allow_threshold.")
        if min_samples_for_automatic < 1:
            raise ValueError("min_samples_for_automatic must be positive.")

        self.pmf = pmf or PMFModel()
        self.pdf = pdf or PDFModel()
        self.jacobian = jacobian or JacobianModel()
        self.hessian = hessian or HessianModel()

        self.allow_threshold = allow_threshold
        self.deny_threshold = deny_threshold
        self.min_samples_for_automatic = min_samples_for_automatic
        self.saddle_margin = saddle_margin

    def observe(self, history: TaskHistory, observation: ActionObservation) -> None:
        history.add(observation)

    def decide(
        self,
        history: TaskHistory,
        family: TaskFamily,
        features: FeatureVector,
        objective: Optional[Callable[[tuple[float, ...]], float]] = None,
    ) -> ApprovalDecision:
        observations = history.for_family(family)

        if not observations:
            return ApprovalDecision(
                label=DecisionLabel.REVIEW,
                approval_probability=0.5,
                confidence=0.0,
                geometry=self._neutral_geometry(),
                reasons=("No historical observations exist for this task family.",),
                family=family,
                sample_count=0,
            )

        probability = self.pmf.estimate(observations)
        confidence = _confidence_from_count(probability.effective_count)

        reasons = [
            f"Historical approval probability estimate: {probability.probability:.4f}.",
            f"Historical observations: {probability.sample_count}.",
        ]

        geometry = self._neutral_geometry()

        if objective is not None:
            geometry = build_geometry_estimate(
                objective,
                features,
                self.jacobian,
                self.hessian,
            )

            reasons.append(
                f"Local gradient/Jacobian norm: {geometry.jacobian_norm:.6g}."
            )
            reasons.append(
                f"Local Hessian norm: {geometry.hessian_norm:.6g}."
            )

            if geometry.near_saddle:
                reasons.append(
                    "Local curvature contains both positive and negative directions; "
                    "automatic approval is suppressed."
                )

        # Sparse history is deliberately conservative.
        if probability.sample_count < self.min_samples_for_automatic:
            reasons.append(
                "Insufficient history for automatic approval; human review required."
            )
            return ApprovalDecision(
                label=DecisionLabel.REVIEW,
                approval_probability=probability.probability,
                confidence=confidence,
                geometry=geometry,
                reasons=tuple(reasons),
                family=family,
                sample_count=probability.sample_count,
            )

        if geometry.near_saddle:
            return ApprovalDecision(
                label=DecisionLabel.REVIEW,
                approval_probability=probability.probability,
                confidence=confidence,
                geometry=geometry,
                reasons=tuple(reasons),
                family=family,
                sample_count=probability.sample_count,
            )

        # Confidence-adjusted probability avoids treating a tiny sample as
        # equivalent to a mature historical distribution.
        effective_score = (
            probability.probability * confidence
            + 0.5 * (1.0 - confidence)
        )

        reasons.append(f"Confidence-adjusted score: {effective_score:.4f}.")

        if effective_score >= self.allow_threshold:
            label = DecisionLabel.ALLOW
            reasons.append("Score crossed the automatic-allow threshold.")
        elif effective_score <= self.deny_threshold:
            label = DecisionLabel.DENY
            reasons.append("Score crossed the deny threshold.")
        else:
            label = DecisionLabel.REVIEW
            reasons.append("Score remains inside the human-review region.")

        return ApprovalDecision(
            label=label,
            approval_probability=probability.probability,
            confidence=confidence,
            geometry=geometry,
            reasons=tuple(reasons),
            family=family,
            sample_count=probability.sample_count,
        )

    @staticmethod
    def _neutral_geometry():
        from .models import GeometryEstimate
        return GeometryEstimate(
            gradient_norm=0.0,
            jacobian_norm=0.0,
            hessian_norm=0.0,
            curvature=0.0,
            condition_indicator=1.0,
            near_saddle=False,
        )


def _confidence_from_count(effective_count: float) -> float:
    # Smoothly approaches 1 without ever claiming certainty.
    return 1.0 - math.exp(-effective_count / 20.0)
