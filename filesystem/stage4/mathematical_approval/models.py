from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


class DecisionLabel(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DENY = "DENY"


@dataclass(frozen=True)
class TaskFamily:
    """Stable identity for a recurring task structure.

    The family key is deliberately separate from task values. For example,
    READ_TABLE -> CALCULATE can remain one family while file paths, columns,
    and numeric values change between sessions.
    """

    key: str
    description: str = ""


@dataclass(frozen=True)
class FeatureVector:
    """Numeric representation consumed by the mathematical layer."""

    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("FeatureVector cannot be empty.")
        if any(not isinstance(x, (int, float)) for x in self.values):
            raise TypeError("FeatureVector values must be numeric.")

    @classmethod
    def from_sequence(cls, values: Sequence[float]) -> "FeatureVector":
        return cls(tuple(float(x) for x in values))


@dataclass(frozen=True)
class ActionObservation:
    """One historical/manual observation.

    approved is the human-reviewed outcome. No filesystem knowledge is stored
    here; callers translate their own task into features and a family key.
    """

    family: TaskFamily
    features: FeatureVector
    approved: bool
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("Observation weight must be positive.")


@dataclass
class TaskHistory:
    """Historical observations for one or more task families."""

    observations: list[ActionObservation] = field(default_factory=list)

    def add(self, observation: ActionObservation) -> None:
        self.observations.append(observation)

    def for_family(self, family: TaskFamily) -> list[ActionObservation]:
        return [o for o in self.observations if o.family.key == family.key]

    def approved_count(self, family: TaskFamily) -> int:
        return sum(o.approved for o in self.for_family(family))

    def rejected_count(self, family: TaskFamily) -> int:
        return sum(not o.approved for o in self.for_family(family))


@dataclass(frozen=True)
class ProbabilityEstimate:
    probability: float
    sample_count: int
    effective_count: float


@dataclass(frozen=True)
class GeometryEstimate:
    gradient_norm: float
    jacobian_norm: float
    hessian_norm: float
    curvature: float
    condition_indicator: float
    near_saddle: bool


@dataclass(frozen=True)
class ApprovalDecision:
    label: DecisionLabel
    approval_probability: float
    confidence: float
    geometry: GeometryEstimate
    reasons: tuple[str, ...]
    family: TaskFamily
    sample_count: int
