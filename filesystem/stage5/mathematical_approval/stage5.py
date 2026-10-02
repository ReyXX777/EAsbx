from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .domain import TaskFamilyDomain
from .ood import DomainOODDetector, OODAssessment
from .representation import DomainAssessment


@dataclass(frozen=True)
class Stage5Assessment:
    decision: str
    domain: DomainAssessment
    ood: OODAssessment
    reason: str


class RepresentationSafetyGate:
    """Stage 5 boundary gate.

    This component deliberately does not perform ALLOW/DENY statistical
    classification. It decides whether a point is representable and inside
    the declared operating domain. Outside that domain -> REVIEW.
    """

    def __init__(self, domain: TaskFamilyDomain, ood_detector: DomainOODDetector | None = None):
        self.domain = domain
        self.ood_detector = ood_detector or DomainOODDetector()

    def assess(self, features: Mapping[str, float]) -> Stage5Assessment:
        domain = self.domain.assess(features)
        ood = self.ood_detector.assess(domain)
        if ood.is_ood:
            return Stage5Assessment(
                "REVIEW", domain, ood,
                "Input is outside the learned/declared operating domain."
            )
        return Stage5Assessment(
            "IN_DOMAIN", domain, ood,
            "Input is inside the declared operating domain."
        )
