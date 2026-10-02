from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .simulation_models import SimulationDecision, SimulationMetrics


def summarize(decisions: Iterable[SimulationDecision]) -> SimulationMetrics:
    return SimulationMetrics.from_decisions(list(decisions))


def metrics_dict(metrics: SimulationMetrics) -> dict[str, int | float]:
    return asdict(metrics)


def format_metrics(metrics: SimulationMetrics) -> str:
    return "\n".join(
        [
            f"Total tasks:          {metrics.total}",
            f"Ground-truth approved:{metrics.approved_truth}",
            f"Ground-truth unsafe:  {metrics.unsafe_truth}",
            f"Predicted ALLOW:      {metrics.predicted_allow}",
            f"Predicted REVIEW:     {metrics.predicted_review}",
            f"Predicted DENY:       {metrics.predicted_deny}",
            f"Accuracy:             {metrics.accuracy:.4f}",
            f"False-allow rate:     {metrics.false_allow_rate:.4f}",
            f"False-deny rate:      {metrics.false_deny_rate:.4f}",
            f"Review rate:          {metrics.review_rate:.4f}",
        ]
    )
