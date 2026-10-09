from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Iterable

from .geometry import HessianModel, JacobianModel, build_geometry_estimate
from .history import LabeledObservation, LabeledTaskHistory
from .models import DecisionLabel, FeatureVector, TaskFamily
from .probability import CategoricalPMFModel, PDFModel
from .simulation_models import GroundTruth


@dataclass(frozen=True)
class Stage4Decision:
    task_id: int
    predicted: DecisionLabel
    truth: GroundTruth
    allow_posterior: float
    deny_posterior: float
    review_probability: float
    allow_log_density: float | None
    deny_log_density: float | None
    nearest_review_distance: float | None
    near_saddle: bool
    route_to_safe_basin: bool


@dataclass(frozen=True)
class Stage4Metrics:
    scenario: str
    seed_pattern: str
    total: int
    accuracy: float
    false_allow_rate: float
    false_deny_rate: float
    review_rate: float
    unsafe_allow_count: int
    approved_deny_count: int
    review_on_unsafe: int
    review_on_approved: int


@dataclass(frozen=True)
class Stage4Report:
    metrics: tuple[Stage4Metrics, ...]
    mean_accuracy: float
    stddev_accuracy: float
    mean_false_allow_rate: float
    mean_safe_automation_rate: float
    conclusion: str


class HistoryAwareApprovalEngine:
    """Three-outcome historical approval model.

    ALLOW and DENY observations form separate local PDFs. REVIEW observations
    are retained as boundary evidence and are never treated as ALLOW evidence.
    A categorical PMF supplies the historical base rates. Jacobian/Hessian
    geometry can suppress automation near saddle regions.
    """

    def __init__(
        self,
        pmf: CategoricalPMFModel | None = None,
        pdf: PDFModel | None = None,
        jacobian: JacobianModel | None = None,
        hessian: HessianModel | None = None,
        allow_threshold: float = 0.80,
        deny_threshold: float = 0.80,
        review_radius: float = 0.75,
        min_class_samples: int = 2,
    ) -> None:
        if not 0.5 < allow_threshold < 1.0:
            raise ValueError("allow_threshold must be between 0.5 and 1.")
        if not 0.5 < deny_threshold < 1.0:
            raise ValueError("deny_threshold must be between 0.5 and 1.")
        if review_radius <= 0:
            raise ValueError("review_radius must be positive.")
        if min_class_samples < 1:
            raise ValueError("min_class_samples must be positive.")

        self.pmf = pmf or CategoricalPMFModel()
        self.pdf = pdf or PDFModel(regularization=0.10)
        self.jacobian = jacobian or JacobianModel()
        self.hessian = hessian or HessianModel()
        self.allow_threshold = allow_threshold
        self.deny_threshold = deny_threshold
        self.review_radius = review_radius
        self.min_class_samples = min_class_samples

    def decide(
        self,
        history: LabeledTaskHistory,
        family: TaskFamily,
        features: FeatureVector,
        objective=None,
    ):
        observations = history.for_family(family)
        allow = [o for o in observations if o.label == DecisionLabel.ALLOW]
        deny = [o for o in observations if o.label == DecisionLabel.DENY]
        review = [o for o in observations if o.label == DecisionLabel.REVIEW]

        probabilities = self.pmf.estimate(
            observations,
            (DecisionLabel.ALLOW, DecisionLabel.REVIEW, DecisionLabel.DENY),
        )

        geometry = None
        if objective is not None:
            geometry = build_geometry_estimate(
                objective, features, self.jacobian, self.hessian
            )

        if len(allow) < self.min_class_samples or len(deny) < self.min_class_samples:
            return DecisionLabel.REVIEW, {
                "allow_posterior": probabilities[DecisionLabel.ALLOW],
                "deny_posterior": probabilities[DecisionLabel.DENY],
                "review_probability": probabilities[DecisionLabel.REVIEW],
                "near_saddle": bool(geometry and geometry.near_saddle),
                "route_to_safe_basin": False,
                "reason": "Both ALLOW and DENY history are required before automatic classification.",
            }

        allow_mean, allow_cov = self.pdf.fit([o.features.values for o in allow])
        deny_mean, deny_cov = self.pdf.fit([o.features.values for o in deny])
        allow_log = self.pdf.log_density(features.values, allow_mean, allow_cov)
        deny_log = self.pdf.log_density(features.values, deny_mean, deny_cov)


        allow_log_prior = math.log(max(probabilities[DecisionLabel.ALLOW], 1e-12))
        deny_log_prior = math.log(max(probabilities[DecisionLabel.DENY], 1e-12))
        allow_score, deny_score = allow_log + allow_log_prior, deny_log + deny_log_prior
        scale = max(allow_score, deny_score)
        allow_mass = math.exp(allow_score - scale)
        deny_mass = math.exp(deny_score - scale)
        total = allow_mass + deny_mass
        allow_post = allow_mass / total
        deny_post = deny_mass / total

        nearest_review = None
        if review:
            nearest_review = min(
                _distance(features.values, o.features.values) for o in review
            )

        saddle = bool(geometry and geometry.near_saddle)
        routed = False
        if saddle:

            routed = self._route_to_safe_basin(features.values, allow_mean)
            return DecisionLabel.REVIEW, {
                "allow_posterior": allow_post,
                "deny_posterior": deny_post,
                "review_probability": probabilities[DecisionLabel.REVIEW],
                "near_saddle": True,
                "route_to_safe_basin": routed,
                "reason": "Saddle geometry suppresses automatic execution; route is review-only.",
            }



        if nearest_review is not None and nearest_review <= self.review_radius:
            return DecisionLabel.REVIEW, {
                "allow_posterior": allow_post,
                "deny_posterior": deny_post,
                "review_probability": probabilities[DecisionLabel.REVIEW],
                "near_saddle": False,
                "route_to_safe_basin": False,
                "reason": "Task lies inside the learned review boundary.",
            }

        if allow_post >= self.allow_threshold and allow_post > deny_post:
            label = DecisionLabel.ALLOW
        elif deny_post >= self.deny_threshold and deny_post > allow_post:
            label = DecisionLabel.DENY
        else:
            label = DecisionLabel.REVIEW

        return label, {
            "allow_posterior": allow_post,
            "deny_posterior": deny_post,
            "review_probability": probabilities[DecisionLabel.REVIEW],
            "near_saddle": False,
            "route_to_safe_basin": False,
            "reason": "Posterior separation did not cross a hard boundary." if label == DecisionLabel.REVIEW else "Posterior crossed the class threshold.",
        }

    @staticmethod
    def _route_to_safe_basin(point, allow_center) -> bool:


        return _distance(point, allow_center) <= 1.0


@dataclass(frozen=True)
class _SyntheticCase:
    task_id: int
    features: FeatureVector
    truth: GroundTruth


class Stage4HistoryHarness:
    """Experiments comparing positive-only history with three-label history."""

    def __init__(self, family: TaskFamily):
        self.family = family

    def run(
        self,
        seed_pattern: str,
        seed: int,
        task_count: int = 1000,
    ) -> Stage4Metrics:
        rng = random.Random(seed)
        history = self._seed_history(seed_pattern)
        engine = HistoryAwareApprovalEngine(min_class_samples=1)

        decisions = []
        for task in self._generate_cases(rng, task_count):
            label, details = engine.decide(history, self.family, task.features)
            decisions.append((label, task.truth))

        total = len(decisions)
        approved = sum(t == GroundTruth.APPROVED for _, t in decisions)
        unsafe = total - approved
        correct = sum(
            (label == DecisionLabel.ALLOW and truth == GroundTruth.APPROVED)
            or (label == DecisionLabel.DENY and truth == GroundTruth.UNSAFE)
            for label, truth in decisions
        )
        false_allow = sum(
            label == DecisionLabel.ALLOW and truth == GroundTruth.UNSAFE
            for label, truth in decisions
        )
        false_deny = sum(
            label == DecisionLabel.DENY and truth == GroundTruth.APPROVED
            for label, truth in decisions
        )
        review_unsafe = sum(
            label == DecisionLabel.REVIEW and truth == GroundTruth.UNSAFE
            for label, truth in decisions
        )
        review_approved = sum(
            label == DecisionLabel.REVIEW and truth == GroundTruth.APPROVED
            for label, truth in decisions
        )
        review_rate = (review_unsafe + review_approved) / total
        safe_automation = sum(
            label == DecisionLabel.ALLOW and truth == GroundTruth.APPROVED
            or label == DecisionLabel.DENY and truth == GroundTruth.UNSAFE
            for label, truth in decisions
        ) / total

        return Stage4Metrics(
            scenario="two-region-history",
            seed_pattern=seed_pattern,
            total=total,
            accuracy=correct / total,
            false_allow_rate=false_allow / unsafe,
            false_deny_rate=false_deny / approved,
            review_rate=review_rate,
            unsafe_allow_count=false_allow,
            approved_deny_count=false_deny,
            review_on_unsafe=review_unsafe,
            review_on_approved=review_approved,
        )

    def repeated(
        self,
        patterns: Iterable[str] = ("2_allow_only", "2_allow_1_deny", "2_allow_1_review", "2_allow_1_deny_1_review"),
        repetitions: int = 25,
        task_count: int = 1000,
    ) -> Stage4Report:
        metrics = [
            self.run(pattern, 7000 + i, task_count)
            for pattern in patterns
            for i in range(repetitions)
        ]
        accuracies = [m.accuracy for m in metrics]
        false_allows = [m.false_allow_rate for m in metrics]
        safe_automation = [1.0 - m.review_rate for m in metrics]
        return Stage4Report(
            metrics=tuple(metrics),
            mean_accuracy=mean(accuracies),
            stddev_accuracy=pstdev(accuracies),
            mean_false_allow_rate=mean(false_allows),
            mean_safe_automation_rate=mean(safe_automation),
            conclusion=(
                "Stage 4 is a boundary-learning experiment, not evidence of production safety. "
                "Compare false-allow rate and review rate across history patterns before integration."
            ),
        )

    def _seed_history(self, pattern: str) -> LabeledTaskHistory:
        history = LabeledTaskHistory()

        history.add(LabeledObservation(self.family, FeatureVector((0.0, 0.0)), DecisionLabel.ALLOW))
        history.add(LabeledObservation(self.family, FeatureVector((0.2, -0.1)), DecisionLabel.ALLOW))

        if pattern in {"2_allow_1_deny", "2_allow_1_deny_1_review"}:
            history.add(LabeledObservation(self.family, FeatureVector((3.0, 3.0)), DecisionLabel.DENY))
        if pattern in {"2_allow_1_review", "2_allow_1_deny_1_review"}:
            history.add(LabeledObservation(self.family, FeatureVector((1.4, 1.4)), DecisionLabel.REVIEW))
        return history

    @staticmethod
    def _generate_cases(rng: random.Random, count: int):
        for i in range(1, count + 1):
            if rng.random() < 0.5:
                point = (
                    rng.gauss(0.0, 0.45),
                    rng.gauss(0.0, 0.45),
                )
                truth = GroundTruth.APPROVED
            else:
                point = (
                    rng.gauss(3.0, 0.55),
                    rng.gauss(3.0, 0.55),
                )
                truth = GroundTruth.UNSAFE
            yield _SyntheticCase(i, FeatureVector(point), truth)


def _distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
