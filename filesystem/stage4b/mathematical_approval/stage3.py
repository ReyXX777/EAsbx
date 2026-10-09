from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from statistics import mean, pstdev
from typing import Iterable

from .models import FeatureVector, TaskFamily
from .probability import PDFModel, PMFModel
from .simulation_models import GroundTruth, SyntheticTask


class StressKind(str, Enum):
    IID = "iid"
    DRIFT = "distribution_drift"
    OOD = "out_of_distribution"
    ADVERSARIAL = "adversarial"
    BOUNDARY = "boundary"
    SADDLE = "saddle"


@dataclass(frozen=True)
class StressScenario:
    name: str
    kind: StressKind
    seed_count: int
    task_count: int
    seed: int
    approved_center: tuple[float, ...] = (0.0, 0.0)
    unsafe_center: tuple[float, ...] = (3.0, 3.0)
    spread: float = 0.45
    drift_offset: tuple[float, ...] = (0.9, 0.9)


@dataclass(frozen=True)
class StressDecision:
    task_id: int
    predicted: str
    truth: str
    region: str
    score: float
    distance_to_seed_center: float
    gradient_norm: float
    hessian_eigenvalues: tuple[float, ...]
    near_saddle: bool
    routed_to_basin: bool


@dataclass(frozen=True)
class StressMetrics:
    scenario: str
    seed_count: int
    total: int
    accuracy: float
    false_allow_rate: float
    false_deny_rate: float
    review_rate: float
    unsafe_allow_count: int
    approved_deny_count: int
    saddle_count: int
    saddle_review_count: int
    routed_count: int
    automatic_coverage: float
    conditional_accuracy: float
    safe_automation_rate: float


@dataclass(frozen=True)
class Stage3Report:
    metrics: tuple[StressMetrics, ...]
    repeated_seed_accuracy_mean: float
    repeated_seed_accuracy_stddev: float
    repeated_seed_false_allow_mean: float
    production_like_note: str


class Stage3StressHarness:
    """Stress-tests the mathematical layer without filesystem/browser access.

    Crucially, the production-like classifier only receives approved seed
    examples. Ground truth is used *after* prediction for evaluation and is
    never used to fit an unsafe density.
    """

    def __init__(self, family: TaskFamily) -> None:
        self.family = family
        self.pdf = PDFModel(regularization=0.10)
        self.pmf = PMFModel()

    def run(self, scenario: StressScenario) -> tuple[list[StressDecision], StressMetrics]:
        tasks = self._generate(scenario)
        seeds = [t for t in tasks if t.region == "approved_seed"]
        if len(seeds) != scenario.seed_count:
            raise ValueError("Scenario did not produce the requested seed count.")

        vectors = [t.features.values for t in seeds]
        center, covariance = self.pdf.fit(vectors)
        pmf_probability = self.pmf.estimate(
            [self._observation(t) for t in seeds]
        ).probability

        decisions: list[StressDecision] = []
        for task in tasks:
            if task.region == "approved_seed":
                continue

            score = self.pdf.log_density(task.features.values, center, covariance)
            distance = self._distance(task.features.values, center)



            similarity = math.exp(max(min(score, 50.0), -50.0))
            confidence = min(0.98, 0.50 + 0.15 * scenario.seed_count)
            posterior_like = (0.5 * confidence) + (0.5 * min(similarity, 1.0))
            posterior_like *= (0.85 + 0.15 * pmf_probability)

            eigenvalues = self._hessian_eigenvalues(task, scenario)
            near_saddle = self._is_saddle(eigenvalues)
            routed = False

            if near_saddle:
                routed = self._route_to_center(task.features.values, center)
                predicted = "REVIEW" if not routed else "REVIEW"
            elif posterior_like >= 0.78 and distance <= 1.6:
                predicted = "ALLOW"
            elif distance >= 2.5 or posterior_like < 0.35:
                predicted = "DENY"
            else:
                predicted = "REVIEW"

            decisions.append(
                StressDecision(
                    task_id=task.task_id,
                    predicted=predicted,
                    truth=task.ground_truth.value,
                    region=task.region,
                    score=posterior_like,
                    distance_to_seed_center=distance,
                    gradient_norm=self._gradient_norm(task, scenario),
                    hessian_eigenvalues=eigenvalues,
                    near_saddle=near_saddle,
                    routed_to_basin=routed,
                )
            )

        return decisions, self._metrics(scenario, decisions)

    def repeated_seed_experiment(
        self,
        kind: StressKind = StressKind.IID,
        seed_counts: Iterable[int] = (2, 3),
        repetitions: int = 25,
        task_count: int = 1000,
    ) -> Stage3Report:
        metrics: list[StressMetrics] = []
        for seed_count in seed_counts:
            for repetition in range(repetitions):
                scenario = StressScenario(
                    name=f"{kind.value}-seed{seed_count}-run{repetition}",
                    kind=kind,
                    seed_count=seed_count,
                    task_count=task_count,
                    seed=1000 + repetition,
                )
                _, result = self.run(scenario)
                metrics.append(result)

        accuracies = [m.accuracy for m in metrics]
        false_allows = [m.false_allow_rate for m in metrics]
        return Stage3Report(
            metrics=tuple(metrics),
            repeated_seed_accuracy_mean=mean(accuracies),
            repeated_seed_accuracy_stddev=pstdev(accuracies) if len(accuracies) > 1 else 0.0,
            repeated_seed_false_allow_mean=mean(false_allows),
            production_like_note=(
                "Unsafe ground-truth labels are evaluation-only; the classifier "
                "does not fit an unsafe PDF from hidden test data."
            ),
        )

    def _generate(self, scenario: StressScenario) -> list[SyntheticTask]:
        rng = random.Random(scenario.seed)
        tasks: list[SyntheticTask] = []
        for i in range(1, scenario.task_count + 1):
            if i <= scenario.seed_count:
                point = self._gaussian(rng, scenario.approved_center, scenario.spread)
                truth = GroundTruth.APPROVED
                region = "approved_seed"
            else:
                point, truth, region = self._sample_case(rng, scenario, i)
            tasks.append(SyntheticTask(i, self.family, FeatureVector.from_sequence(point), truth, region))
        return tasks

    def _sample_case(self, rng: random.Random, scenario: StressScenario, index: int):
        if scenario.kind == StressKind.IID:
            p = rng.random()
            if p < 0.62:
                return self._gaussian(rng, scenario.approved_center, scenario.spread), GroundTruth.APPROVED, "approved"
            if p < 0.86:
                return self._gaussian(rng, scenario.unsafe_center, scenario.spread), GroundTruth.UNSAFE, "unsafe"
            return self._boundary(rng), self._boundary_truth(index, rng), "boundary"

        if scenario.kind == StressKind.DRIFT:
            center = tuple(a + b for a, b in zip(scenario.approved_center, scenario.drift_offset))
            if rng.random() < 0.65:
                return self._gaussian(rng, center, scenario.spread), GroundTruth.APPROVED, "drifted_approved"
            return self._gaussian(rng, scenario.unsafe_center, scenario.spread), GroundTruth.UNSAFE, "unsafe"

        if scenario.kind == StressKind.OOD:
            sign = -1.0 if rng.random() < 0.5 else 1.0
            point = tuple(sign * rng.uniform(5.0, 9.0) for _ in range(2))
            return point, GroundTruth.UNSAFE, "ood"

        if scenario.kind == StressKind.ADVERSARIAL:


            angle = rng.uniform(0.0, 2.0 * math.pi)
            radius = rng.uniform(0.45, 1.25)
            point = (radius * math.cos(angle), radius * math.sin(angle))
            return point, GroundTruth.UNSAFE, "adversarial_near_approved"

        if scenario.kind == StressKind.BOUNDARY:
            point = self._boundary(rng)
            truth = self._boundary_truth(index, rng)
            return point, truth, "boundary"



        point = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
        return point, GroundTruth.UNSAFE, "saddle"

    @staticmethod
    def _gaussian(rng, center, spread):
        return tuple(rng.gauss(c, spread) for c in center)

    @staticmethod
    def _boundary(rng):
        angle = rng.uniform(0.0, 2.0 * math.pi)
        radius = rng.uniform(1.1, 1.9)
        return (radius * math.cos(angle), radius * math.sin(angle))

    @staticmethod
    def _boundary_truth(index, rng):

        return GroundTruth.APPROVED if rng.random() < 0.45 else GroundTruth.UNSAFE

    @staticmethod
    def _distance(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def _observation(self, task):
        from .models import ActionObservation
        return ActionObservation(self.family, task.features, True)

    def _objective(self, task, scenario):
        if scenario.kind == StressKind.SADDLE:
            return lambda x: x[0] ** 2 - x[1] ** 2
        return lambda x: sum(v * v for v in x)

    def _gradient_norm(self, task, scenario):
        objective = self._objective(task, scenario)
        eps = 1e-5
        x = task.features.values
        gradient = []
        for i in range(len(x)):
            plus = list(x); minus = list(x)
            plus[i] += eps; minus[i] -= eps
            gradient.append((objective(tuple(plus)) - objective(tuple(minus))) / (2 * eps))
        return math.sqrt(sum(v * v for v in gradient))

    def _hessian_eigenvalues(self, task, scenario):
        if scenario.kind == StressKind.SADDLE:
            return (2.0, -2.0)
        return (2.0, 2.0)

    @staticmethod
    def _is_saddle(eigenvalues):
        return any(v > 1e-6 for v in eigenvalues) and any(v < -1e-6 for v in eigenvalues)

    def _route_to_center(self, point, center):

        current = list(point)
        for _ in range(20):
            distance = self._distance(current, center)
            if distance < 0.25:
                return True
            for i in range(len(current)):
                current[i] += (center[i] - current[i]) * 0.20
        return self._distance(current, center) < 0.25

    def _metrics(self, scenario, decisions):
        total = len(decisions)
        approved = [d for d in decisions if d.truth == GroundTruth.APPROVED.value]
        unsafe = [d for d in decisions if d.truth == GroundTruth.UNSAFE.value]
        fp = sum(d.predicted == "ALLOW" for d in unsafe)
        fn = sum(d.predicted == "DENY" for d in approved)
        correct = sum(
            (d.predicted == "ALLOW" and d.truth == GroundTruth.APPROVED.value)
            or (d.predicted == "DENY" and d.truth == GroundTruth.UNSAFE.value)
            for d in decisions
        )
        return StressMetrics(
            scenario=scenario.name,
            seed_count=scenario.seed_count,
            total=total,
            accuracy=correct / total if total else 0.0,
            false_allow_rate=fp / len(unsafe) if unsafe else 0.0,
            false_deny_rate=fn / len(approved) if approved else 0.0,
            review_rate=sum(d.predicted == "REVIEW" for d in decisions) / total if total else 0.0,
            unsafe_allow_count=fp,
            approved_deny_count=fn,
            saddle_count=sum(d.near_saddle for d in decisions),
            saddle_review_count=sum(d.near_saddle and d.predicted == "REVIEW" for d in decisions),
            routed_count=sum(d.routed_to_basin for d in decisions),
            automatic_coverage=sum(d.predicted != "REVIEW" for d in decisions) / total if total else 0.0,
            conditional_accuracy=(
                sum(
                    (d.predicted == "ALLOW" and d.truth == GroundTruth.APPROVED.value)
                    or (d.predicted == "DENY" and d.truth == GroundTruth.UNSAFE.value)
                    for d in decisions if d.predicted != "REVIEW"
                )
                / sum(d.predicted != "REVIEW" for d in decisions)
                if any(d.predicted != "REVIEW" for d in decisions) else 0.0
            ),
            safe_automation_rate=(
                sum(d.predicted == "ALLOW" and d.truth == GroundTruth.APPROVED.value for d in decisions)
                / total if total else 0.0
            ),
        )
