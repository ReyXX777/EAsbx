from __future__ import annotations

from dataclasses import dataclass
import math

from .representation import DomainAssessment


@dataclass(frozen=True)
class OODAssessment:
    is_ood: bool
    score: float
    reasons: tuple[str, ...]


class DomainOODDetector:
    """Conservative OOD gate.

    Explicit feature-domain violations are always OOD. A configurable
    normalized-distance threshold catches values that remain inside hard
    bounds but are too far from the declared operating center.
    """

    def __init__(self, distance_threshold: float = 3.0) -> None:
        if distance_threshold <= 0:
            raise ValueError("distance_threshold must be positive")
        self.distance_threshold = distance_threshold

    def assess(self, domain: DomainAssessment) -> OODAssessment:
        reasons = list(domain.violations)
        if domain.distance > self.distance_threshold:
            reasons.append("normalized-distance-exceeded")
        return OODAssessment(
            is_ood=bool(reasons),
            score=domain.distance,
            reasons=tuple(reasons),
        )
