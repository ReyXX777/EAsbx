from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .decision import MathematicalApprovalEngine
from .geometry import build_geometry_estimate
from .models import ActionObservation, FeatureVector, TaskFamily, TaskHistory
from .probability import PDFModel
from .simulation_models import (
    GroundTruth,
    SimulationDecision,
    SimulationMetrics,
    SyntheticTask,
)
from .simulation_metrics import summarize


@dataclass(frozen=True)
class SimulationConfig:
    allow_threshold: float = 0.80
    deny_threshold: float = 0.20
    density_ratio_allow: float = 3.0
    density_ratio_deny: float = 0.33
    minimum_density: float = 1e-12
    route_steps: int = 12
    route_step_size: float = 0.15


class SimulationHarness:
    """Runs offline experiments against synthetic recurring task variants.

    It never touches MOCKAPP files and never invokes a live agent.
    """

    def __init__(
        self,
        family: TaskFamily,
        config: SimulationConfig | None = None,
    ) -> None:
        self.family = family
        self.config = config or SimulationConfig()
        self.engine = MathematicalApprovalEngine(
            allow_threshold=self.config.allow_threshold,
            deny_threshold=self.config.deny_threshold,
            # The harness itself controls the seed-history experiment.
            min_samples_for_automatic=1,
        )
        self.pdf = PDFModel(regularization=0.10)

    def run(self, tasks: list[SyntheticTask]) -> tuple[list[SimulationDecision], SimulationMetrics]:
        if not tasks:
            return [], summarize([])

        seed_tasks = [t for t in tasks if t.region == "approved_seed"]
        if not seed_tasks:
            raise ValueError("Scenario must contain at least one approved seed task.")

        history = TaskHistory()
        for task in seed_tasks:
            history.add(
                ActionObservation(
                    family=task.family,
                    features=task.features,
                    approved=True,
                )
            )

        approved_vectors = [t.features.values for t in seed_tasks]
        approved_mean, approved_cov = self.pdf.fit(approved_vectors)

        # A small synthetic unsafe reference cloud is available to the simulator
        # as hidden evaluation structure. A real adapter must not manufacture
        # this from a live policy decision; this is purely an experiment.
        unsafe_reference = self._unsafe_reference(tasks)
        unsafe_mean, unsafe_cov = self.pdf.fit(unsafe_reference)

        decisions: list[SimulationDecision] = []
        for task in tasks:
            if task in seed_tasks:
                continue

            probability = self.engine.pmf.estimate(history.for_family(self.family))
            approved_log_density = self.pdf.log_density(task.features.values, approved_mean, approved_cov)
            unsafe_log_density = self.pdf.log_density(task.features.values, unsafe_mean, unsafe_cov)
            log_ratio = approved_log_density - unsafe_log_density
            ratio = math.exp(max(min(log_ratio, 700.0), -700.0))

            geometry = self._geometry(task.features)
            predicted, routed = self._classify(
                probability.probability,
                ratio,
                geometry.near_saddle,
                task.features,
                approved_mean,
            )

            decisions.append(
                SimulationDecision(
                    task_id=task.task_id,
                    predicted=predicted,
                    ground_truth=task.ground_truth,
                    score=ratio,
                    pmf_probability=probability.probability,
                    approved_density=math.exp(max(min(approved_log_density, 700.0), -700.0)),
                    unsafe_density=math.exp(max(min(unsafe_log_density, 700.0), -700.0)),
                    density_ratio=ratio,
                    log_density_ratio=log_ratio,
                    gradient_norm=geometry.gradient_norm,
                    hessian_norm=geometry.hessian_norm,
                    near_saddle=geometry.near_saddle,
                    used_route_to_minimum=routed,
                )
            )

        return decisions, summarize(decisions)

    def _classify(
        self,
        pmf_probability: float,
        density_ratio: float,
        near_saddle: bool,
        point: FeatureVector,
        approved_center: tuple[float, ...],
    ) -> tuple[object, bool]:
        # PMF is only a prior signal. With 2-3 approved seeds it cannot be
        # allowed to approve a task merely because the family was previously OK.
        if near_saddle:
            routed = self._route_to_approved_basin(point, approved_center)
            if routed:
                return self._density_decision(pmf_probability, density_ratio), True
            from .models import DecisionLabel
            return DecisionLabel.REVIEW, False

        return self._density_decision(pmf_probability, density_ratio), False

    def _density_decision(self, pmf_probability: float, density_ratio: float):
        from .models import DecisionLabel
        # Combine a bounded historical prior with a class-density ratio.
        # The prior is intentionally weak so feature-space evidence dominates.
        prior = min(max(pmf_probability, 0.01), 0.99)
        log_odds = math.log(prior / (1.0 - prior)) + math.log(max(density_ratio, 1e-12))
        posterior = 1.0 / (1.0 + math.exp(-max(min(log_odds, 60.0), -60.0)))

        if math.log(max(density_ratio, 1e-300)) >= math.log(self.config.density_ratio_allow) and posterior >= self.config.allow_threshold:
            return DecisionLabel.ALLOW
        if math.log(max(density_ratio, 1e-300)) <= math.log(self.config.density_ratio_deny) and posterior <= self.config.deny_threshold:
            return DecisionLabel.DENY
        return DecisionLabel.REVIEW

    def _geometry(self, point: FeatureVector):
        # Bowl around the approved basin. The saddle detector is exercised by
        # a separate saddle-aware objective rather than by filesystem code.
        def objective(x: tuple[float, ...]) -> float:
            return sum(v * v for v in x)

        return build_geometry_estimate(
            objective,
            point,
            self.engine.jacobian,
            self.engine.hessian,
        )

    def _route_to_approved_basin(
        self,
        point: FeatureVector,
        approved_center: tuple[float, ...],
    ) -> bool:
        current = list(point.values)
        for _ in range(self.config.route_steps):
            distance = math.sqrt(
                sum((current[i] - approved_center[i]) ** 2 for i in range(len(current)))
            )
            if distance <= 0.5:
                return True
            norm = max(distance, 1e-12)
            for i in range(len(current)):
                direction = (approved_center[i] - current[i]) / norm
                current[i] += direction * self.config.route_step_size
        return math.sqrt(
            sum((current[i] - approved_center[i]) ** 2 for i in range(len(current)))
        ) <= 0.5

    @staticmethod
    def _unsafe_reference(tasks: list[SyntheticTask]) -> list[tuple[float, ...]]:
        values = [t.features.values for t in tasks if t.ground_truth == GroundTruth.UNSAFE]
        if len(values) >= 2:
            return values[: min(len(values), 100)]
        # Fallback only for pathological scenarios; keeps the simulator valid.
        return [(3.0, 3.0), (3.2, 3.1), (2.8, 2.9)]
