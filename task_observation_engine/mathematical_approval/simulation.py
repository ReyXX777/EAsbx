from __future__ import annotations

import random

from .decision import MathematicalApprovalEngine
from .models import ActionObservation, FeatureVector, TaskFamily, TaskHistory


def make_repeated_history(
    family: TaskFamily,
    approved: int,
    rejected: int,
    dimension: int = 2,
    seed: int = 7,
) -> TaskHistory:
    """Generate deterministic synthetic history for development/testing."""
    rng = random.Random(seed)
    history = TaskHistory()

    for _ in range(approved):
        features = FeatureVector.from_sequence(
            rng.gauss(0.0, 0.25) for _ in range(dimension)
        )
        history.add(ActionObservation(family, features, True))

    for _ in range(rejected):
        features = FeatureVector.from_sequence(
            rng.gauss(2.0, 0.25) for _ in range(dimension)
        )
        history.add(ActionObservation(family, features, False))

    return history


def run_demo() -> dict[str, object]:
    family = TaskFamily("filesystem.read_table.calculate")
    history = make_repeated_history(family, approved=40, rejected=2)

    engine = MathematicalApprovalEngine(min_samples_for_automatic=10)
    candidate = FeatureVector.from_sequence((0.1, -0.1))


    def objective(x: tuple[float, ...]) -> float:
        return sum(v * v for v in x)

    decision = engine.decide(
        history,
        family,
        candidate,
        objective=objective,
    )

    return {
        "label": decision.label.value,
        "approval_probability": decision.approval_probability,
        "confidence": decision.confidence,
        "sample_count": decision.sample_count,
        "reasons": decision.reasons,
    }


if __name__ == "__main__":
    print(run_demo())
