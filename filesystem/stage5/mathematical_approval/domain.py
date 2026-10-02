from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .representation import DomainAssessment, FeatureNormalizer, FeatureSpec


@dataclass(frozen=True)
class TaskFamilyDomain:
    family: str
    normalizer: FeatureNormalizer

    @classmethod
    def from_specs(cls, family: str, specs: Sequence[FeatureSpec]) -> "TaskFamilyDomain":
        return cls(family, FeatureNormalizer(family, specs))

    def assess(self, features: Mapping[str, float]) -> DomainAssessment:
        return self.normalizer.assess(features)

    def normalize(self, features: Mapping[str, float]):
        return self.normalizer.transform(features)
