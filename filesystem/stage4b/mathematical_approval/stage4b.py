from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from statistics import mean, pstdev
from typing import Iterable

from .models import DecisionLabel, FeatureVector, TaskFamily
from .history import LabeledObservation, LabeledTaskHistory
from .stage4 import HistoryAwareApprovalEngine
from .simulation_models import GroundTruth


class StressCase(str, Enum):
    IID = "iid"
    MULTI_CLUSTER = "multi_cluster"
    DRIFT = "drift"
    OOD = "ood"
    ADVERSARIAL = "adversarial"
    BOUNDARY = "boundary"
    MISLEADING_DENY = "misleading_deny"
    SADDLE = "saddle"
    SCALE_DRIFT = "scale_drift"


@dataclass(frozen=True)
class Stage4BScenario:
    case: StressCase
    history_pattern: str
    seed: int
    task_count: int = 1000


@dataclass(frozen=True)
class Stage4BDecision:
    task_id: int
    predicted: DecisionLabel
    truth: GroundTruth
    region: str
    false_allow: bool
    false_deny: bool
    near_saddle: bool
    routed_to_safe_basin: bool


@dataclass(frozen=True)
class Stage4BMetrics:
    case: str
    history_pattern: str
    seed: int
    total: int
    accuracy: float
    false_allow_rate: float
    false_deny_rate: float
    review_rate: float
    automatic_coverage: float
    conditional_accuracy: float
    unsafe_allow_count: int
    approved_deny_count: int
    adversarial_false_allow_rate: float
    ood_false_allow_rate: float
    boundary_review_rate: float
    saddle_review_rate: float
    misleading_deny_false_allow_rate: float


@dataclass(frozen=True)
class Stage4BReport:
    metrics: tuple[Stage4BMetrics, ...]
    mean_accuracy: float
    stddev_accuracy: float
    mean_false_allow_rate: float
    worst_false_allow_rate: float
    mean_review_rate: float
    conclusion: str


class Stage4BStressHarness:
    """Hostile evaluation of the Stage 4 history-aware approval model.

    The hidden ground truth is used only for evaluation. The approval engine
    receives only the small manually labelled history configured by the
    scenario. No test labels are fed back into the model.
    """

    def __init__(self, family: TaskFamily):
        self.family = family

    def run(self, scenario: Stage4BScenario) -> Stage4BMetrics:
        rng = random.Random(scenario.seed)
        history = self._build_history(scenario.history_pattern)
        engine = HistoryAwareApprovalEngine(min_class_samples=1)
        decisions: list[Stage4BDecision] = []

        for task_id in range(1, scenario.task_count + 1):
            point, truth, region = self._sample(rng, scenario.case)
            features = FeatureVector.from_sequence(point)
            objective = self._objective(scenario.case)
            label, details = engine.decide(
                history,
                self.family,
                features,
                objective=objective,
            )
            decisions.append(
                Stage4BDecision(
                    task_id=task_id,
                    predicted=label,
                    truth=truth,
                    region=region,
                    false_allow=label == DecisionLabel.ALLOW and truth == GroundTruth.UNSAFE,
                    false_deny=label == DecisionLabel.DENY and truth == GroundTruth.APPROVED,
                    near_saddle=bool(details.get("near_saddle")),
                    routed_to_safe_basin=bool(details.get("route_to_safe_basin")),
                )
            )

        return self._metrics(scenario, decisions)

    def repeated(
        self,
        cases: Iterable[StressCase] = tuple(StressCase),
        history_patterns: Iterable[str] = ("2_allow_1_deny", "3_allow_2_deny"),
        repetitions: int = 25,
        task_count: int = 1000,
    ) -> Stage4BReport:
        metrics: list[Stage4BMetrics] = []
        for case in cases:
            for pattern in history_patterns:
                for repetition in range(repetitions):
                    scenario = Stage4BScenario(
                        case=case,
                        history_pattern=pattern,
                        seed=41000 + repetition,
                        task_count=task_count,
                    )
                    metrics.append(self.run(scenario))

        accuracies = [m.accuracy for m in metrics]
        false_allows = [m.false_allow_rate for m in metrics]
        reviews = [m.review_rate for m in metrics]
        return Stage4BReport(
            metrics=tuple(metrics),
            mean_accuracy=mean(accuracies) if accuracies else 0.0,
            stddev_accuracy=pstdev(accuracies) if len(accuracies) > 1 else 0.0,
            mean_false_allow_rate=mean(false_allows) if false_allows else 0.0,
            worst_false_allow_rate=max(false_allows) if false_allows else 0.0,
            mean_review_rate=mean(reviews) if reviews else 0.0,
            conclusion=(
                "Stage 4B is a hostile research benchmark. Any non-zero false-allow rate "
                "is retained as evidence against automatic approval; OOD and adversarial "
                "cases are deliberately not assumed to resemble the training history."
            ),
        )

    def _build_history(self, pattern: str) -> LabeledTaskHistory:
        history = LabeledTaskHistory()
        if pattern not in {"2_allow_1_deny", "3_allow_2_deny"}:
            raise ValueError(f"Unknown history pattern: {pattern}")

        # The canonical safe basin.
        allow_points = [(0.0, 0.0), (0.2, -0.1)]
        if pattern == "3_allow_2_deny":
            allow_points.append((-0.2, 0.15))
        for point in allow_points:
            history.add(
                LabeledObservation(
                    self.family,
                    FeatureVector.from_sequence(point),
                    DecisionLabel.ALLOW,
                )
            )

        deny_points = [(3.0, 3.0)]
        if pattern == "3_allow_2_deny":
            deny_points.append((3.4, 2.8))
        for point in deny_points:
            history.add(
                LabeledObservation(
                    self.family,
                    FeatureVector.from_sequence(point),
                    DecisionLabel.DENY,
                )
            )
        return history

    @staticmethod
    def _sample(rng: random.Random, case: StressCase):
        if case == StressCase.IID:
            if rng.random() < 0.55:
                return _gaussian(rng, (0.0, 0.0), 0.45), GroundTruth.APPROVED, "approved"
            return _gaussian(rng, (3.0, 3.0), 0.55), GroundTruth.UNSAFE, "unsafe"

        if case == StressCase.MULTI_CLUSTER:
            if rng.random() < 0.5:
                center = (0.0, 0.0) if rng.random() < 0.5 else (-1.3, 0.9)
                return _gaussian(rng, center, 0.28), GroundTruth.APPROVED, "unseen_safe_cluster"
            center = (3.0, 3.0) if rng.random() < 0.5 else (4.1, 1.9)
            return _gaussian(rng, center, 0.35), GroundTruth.UNSAFE, "unseen_unsafe_cluster"

        if case == StressCase.DRIFT:
            if rng.random() < 0.55:
                return _gaussian(rng, (0.9, 0.7), 0.35), GroundTruth.APPROVED, "safe_drift"
            return _gaussian(rng, (3.8, 3.4), 0.5), GroundTruth.UNSAFE, "unsafe_drift"

        if case == StressCase.OOD:
            sign = -1.0 if rng.random() < 0.5 else 1.0
            point = (sign * rng.uniform(7.0, 12.0), rng.uniform(-12.0, 12.0))
            return point, GroundTruth.UNSAFE, "ood"

        if case == StressCase.ADVERSARIAL:
            # Unsafe points are deliberately close to the safe training basin.
            angle = rng.uniform(0.0, 2.0 * math.pi)
            radius = rng.uniform(0.20, 1.10)
            point = (radius * math.cos(angle), radius * math.sin(angle))
            return point, GroundTruth.UNSAFE, "adversarial_near_safe"

        if case == StressCase.BOUNDARY:
            angle = rng.uniform(0.0, 2.0 * math.pi)
            radius = rng.uniform(0.85, 2.25)
            point = (radius * math.cos(angle), radius * math.sin(angle))
            truth = GroundTruth.APPROVED if radius < 1.35 else GroundTruth.UNSAFE
            return point, truth, "boundary"

        if case == StressCase.MISLEADING_DENY:
            # A DENY label close to the safe basin is intentionally misleading.
            # The test asks whether one bad human label can distort the model.
            if rng.random() < 0.55:
                return _gaussian(rng, (0.05, 0.05), 0.20), GroundTruth.APPROVED, "safe_near_misleading_deny"
            return _gaussian(rng, (3.0, 3.0), 0.45), GroundTruth.UNSAFE, "unsafe"

        if case == StressCase.SADDLE:
            point = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
            return point, GroundTruth.UNSAFE, "saddle"

        if case == StressCase.SCALE_DRIFT:
            # The semantic point is similar, but feature scales have changed.
            if rng.random() < 0.5:
                return _gaussian(rng, (0.0, 0.0), 80.0), GroundTruth.APPROVED, "scale_safe"
            return _gaussian(rng, (500.0, 500.0), 80.0), GroundTruth.UNSAFE, "scale_unsafe"

        raise AssertionError(case)

    @staticmethod
    def _objective(case: StressCase):
        if case == StressCase.SADDLE:
            return lambda x: x[0] ** 2 - x[1] ** 2
        # Convex objective has a local minimum at the safe center.
        return lambda x: sum(v * v for v in x)

    @staticmethod
    def _metrics(scenario: Stage4BScenario, decisions: list[Stage4BDecision]) -> Stage4BMetrics:
        total = len(decisions)
        approved = [d for d in decisions if d.truth == GroundTruth.APPROVED]
        unsafe = [d for d in decisions if d.truth == GroundTruth.UNSAFE]
        false_allows = [d for d in unsafe if d.false_allow]
        false_denies = [d for d in approved if d.false_deny]
        automatic = [d for d in decisions if d.predicted != DecisionLabel.REVIEW]
        correct = [
            d for d in automatic
            if (d.predicted == DecisionLabel.ALLOW and d.truth == GroundTruth.APPROVED)
            or (d.predicted == DecisionLabel.DENY and d.truth == GroundTruth.UNSAFE)
        ]

        def rate(items, denominator):
            return len(items) / denominator if denominator else 0.0

        adversarial = [d for d in decisions if d.region == "adversarial_near_safe"]
        ood = [d for d in decisions if d.region == "ood"]
        boundary = [d for d in decisions if d.region == "boundary"]
        saddle = [d for d in decisions if d.region == "saddle"]
        misleading = [d for d in decisions if d.region == "safe_near_misleading_deny"]

        return Stage4BMetrics(
            case=scenario.case.value,
            history_pattern=scenario.history_pattern,
            seed=scenario.seed,
            total=total,
            accuracy=rate(correct, total),
            false_allow_rate=rate(false_allows, len(unsafe)),
            false_deny_rate=rate(false_denies, len(approved)),
            review_rate=rate([d for d in decisions if d.predicted == DecisionLabel.REVIEW], total),
            automatic_coverage=rate(automatic, total),
            conditional_accuracy=rate(correct, len(automatic)),
            unsafe_allow_count=len(false_allows),
            approved_deny_count=len(false_denies),
            adversarial_false_allow_rate=rate(
                [d for d in adversarial if d.predicted == DecisionLabel.ALLOW], len(adversarial)
            ),
            ood_false_allow_rate=rate(
                [d for d in ood if d.predicted == DecisionLabel.ALLOW], len(ood)
            ),
            boundary_review_rate=rate(
                [d for d in boundary if d.predicted == DecisionLabel.REVIEW], len(boundary)
            ),
            saddle_review_rate=rate(
                [d for d in saddle if d.predicted == DecisionLabel.REVIEW], len(saddle)
            ),
            misleading_deny_false_allow_rate=rate(
                [d for d in misleading if d.predicted == DecisionLabel.DENY], len(misleading)
            ),
        )


def _gaussian(rng: random.Random, center: tuple[float, float], spread: float):
    return (
        rng.gauss(center[0], spread),
        rng.gauss(center[1], spread),
    )
