from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import DecisionLabel, FeatureVector, TaskFamily


@dataclass(frozen=True)
class LabeledObservation:
    """One human-labelled historical task.

    REVIEW is intentionally preserved as boundary/uncertainty evidence. It is
    not folded into ALLOW or DENY training data.
    """

    family: TaskFamily
    features: FeatureVector
    label: DecisionLabel
    weight: float = 1.0
    session_id: str | None = None

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("Observation weight must be positive.")


@dataclass
class LabeledTaskHistory:
    observations: list[LabeledObservation] = field(default_factory=list)

    def add(self, observation: LabeledObservation) -> None:
        self.observations.append(observation)

    def extend(self, observations: Iterable[LabeledObservation]) -> None:
        self.observations.extend(observations)

    def for_family(self, family: TaskFamily) -> list[LabeledObservation]:
        return [o for o in self.observations if o.family.key == family.key]

    def for_label(self, family: TaskFamily, label: DecisionLabel) -> list[LabeledObservation]:
        return [o for o in self.for_family(family) if o.label == label]

    def count(self, family: TaskFamily, label: DecisionLabel) -> int:
        return len(self.for_label(family, label))

    def weight(self, family: TaskFamily, label: DecisionLabel) -> float:
        return sum(o.weight for o in self.for_label(family, label))
