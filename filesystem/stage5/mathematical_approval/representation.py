from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


class RepresentationError(ValueError):
    pass


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    minimum: float | None = None
    maximum: float | None = None
    center: float | None = None
    scale: float | None = None

    def validate(self) -> None:
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise RepresentationError(f"Invalid bounds for feature {self.name!r}.")
        if self.scale is not None and (not math.isfinite(self.scale) or self.scale <= 0):
            raise RepresentationError(f"Scale must be positive for feature {self.name!r}.")


@dataclass(frozen=True)
class FeatureVector:
    names: tuple[str, ...]
    values: tuple[float, ...]
    family: str

    def as_mapping(self) -> dict[str, float]:
        return dict(zip(self.names, self.values))


@dataclass(frozen=True)
class DomainAssessment:
    in_domain: bool
    distance: float
    violations: tuple[str, ...]
    normalized: FeatureVector


class FeatureNormalizer:
    """Deterministic representation layer.

    Raw task values are mapped into a fixed, named numerical space. Explicit
    domain bounds are checked before statistical approval logic is consulted.
    """

    def __init__(self, family: str, specs: Sequence[FeatureSpec]) -> None:
        if not family.strip():
            raise RepresentationError("Task family cannot be empty.")
        if not specs:
            raise RepresentationError("At least one feature is required.")
        self.family = family
        self.specs = tuple(specs)
        names = [s.name for s in self.specs]
        if len(set(names)) != len(names):
            raise RepresentationError("Feature names must be unique.")
        for spec in self.specs:
            spec.validate()

    def transform(self, raw: Mapping[str, float]) -> FeatureVector:
        values = []
        for spec in self.specs:
            if spec.name not in raw:
                raise RepresentationError(f"Missing feature: {spec.name}")
            value = float(raw[spec.name])
            if not math.isfinite(value):
                raise RepresentationError(f"Non-finite feature: {spec.name}")
            center = spec.center if spec.center is not None else (
                ((spec.minimum + spec.maximum) / 2)
                if spec.minimum is not None and spec.maximum is not None
                else 0.0
            )
            scale = spec.scale if spec.scale is not None else (
                ((spec.maximum - spec.minimum) / 2)
                if spec.minimum is not None and spec.maximum is not None and spec.maximum > spec.minimum
                else 1.0
            )
            if scale <= 0:
                scale = 1.0
            values.append((value - center) / scale)
        return FeatureVector(tuple(s.name for s in self.specs), tuple(values), self.family)

    def assess(self, raw: Mapping[str, float]) -> DomainAssessment:
        normalized = self.transform(raw)
        violations = []
        distance_sq = 0.0
        for spec, value in zip(self.specs, raw_values := [float(raw[s.name]) for s in self.specs]):
            if spec.minimum is not None and value < spec.minimum:
                violations.append(f"{spec.name}<minimum")
            if spec.maximum is not None and value > spec.maximum:
                violations.append(f"{spec.name}>maximum")
            center = spec.center if spec.center is not None else (
                ((spec.minimum + spec.maximum) / 2)
                if spec.minimum is not None and spec.maximum is not None
                else 0.0
            )
            scale = spec.scale if spec.scale is not None else (
                ((spec.maximum - spec.minimum) / 2)
                if spec.minimum is not None and spec.maximum is not None and spec.maximum > spec.minimum
                else 1.0
            )
            scale = scale if scale > 0 else 1.0
            distance_sq += ((value - center) / scale) ** 2
        return DomainAssessment(
            in_domain=not violations,
            distance=math.sqrt(distance_sq),
            violations=tuple(violations),
            normalized=normalized,
        )
