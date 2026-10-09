from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .models import FeatureVector, TaskFamily
from .simulation_models import GroundTruth, SyntheticTask


@dataclass(frozen=True)
class ScenarioConfig:
    task_count: int = 1000
    seed_count: int = 3
    seed: int = 42
    dimension: int = 2
    approved_center: tuple[float, ...] = (0.0, 0.0)
    unsafe_center: tuple[float, ...] = (3.0, 3.0)
    spread: float = 0.45
    borderline_radius: float = 1.35


class SyntheticTaskFamilyGenerator:
    """Generate recurring task variations with fixed structure and changing values."""

    def __init__(self, family: TaskFamily, config: ScenarioConfig | None = None) -> None:
        self.family = family
        self.config = config or ScenarioConfig()
        if len(self.config.approved_center) != self.config.dimension:
            raise ValueError("approved_center dimension mismatch")
        if len(self.config.unsafe_center) != self.config.dimension:
            raise ValueError("unsafe_center dimension mismatch")

    def generate(self) -> list[SyntheticTask]:
        rng = random.Random(self.config.seed)
        tasks: list[SyntheticTask] = []


        for task_id in range(1, self.config.task_count + 1):
            phase = rng.random()
            if task_id <= self.config.seed_count:
                features = self._sample_gaussian(rng, self.config.approved_center)
                truth = GroundTruth.APPROVED
                region = "approved_seed"
            elif phase < 0.62:
                features = self._sample_gaussian(rng, self.config.approved_center)
                truth = GroundTruth.APPROVED
                region = "approved"
            elif phase < 0.86:
                features = self._sample_gaussian(rng, self.config.unsafe_center)
                truth = GroundTruth.UNSAFE
                region = "unsafe"
            else:
                features = self._sample_borderline(rng)

                truth = (
                    GroundTruth.APPROVED
                    if self._distance(features.values, self.config.approved_center)
                    < self.config.borderline_radius
                    else GroundTruth.UNSAFE
                )
                region = "borderline"

            tasks.append(
                SyntheticTask(
                    task_id=task_id,
                    family=self.family,
                    features=features,
                    ground_truth=truth,
                    region=region,
                )
            )

        return tasks

    def _sample_gaussian(
        self,
        rng: random.Random,
        center: tuple[float, ...],
    ) -> FeatureVector:
        return FeatureVector.from_sequence(
            rng.gauss(center[i], self.config.spread)
            for i in range(self.config.dimension)
        )

    def _sample_borderline(self, rng: random.Random) -> FeatureVector:
        angle = rng.uniform(0.0, 2.0 * math.pi)
        radius = rng.uniform(0.8, 2.1)
        values = [radius * math.cos(angle), radius * math.sin(angle)]
        if self.config.dimension > 2:
            values.extend(rng.gauss(0.0, 0.25) for _ in range(self.config.dimension - 2))
        return FeatureVector.from_sequence(values)

    @staticmethod
    def _distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
