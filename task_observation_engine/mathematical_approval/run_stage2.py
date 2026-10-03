from __future__ import annotations

import json

from task_observation_engine.mathematical_approval.mathematical_approval.models import (
    TaskFamily,
)
from task_observation_engine.mathematical_approval.mathematical_approval.simulation_metrics import (
    format_metrics,
)
from task_observation_engine.mathematical_approval.mathematical_approval.simulation_runner import (
    SimulationHarness,
)
from task_observation_engine.mathematical_approval.mathematical_approval.simulation_scenarios import (
    ScenarioConfig,
    SyntheticTaskFamilyGenerator,
)


def main() -> None:
    family = TaskFamily(
        key="filesystem.read_table.calculate",
        description="Stable READ_TABLE -> CALCULATE structure with changing values.",
    )

    scenario = ScenarioConfig(
        task_count=1000,
        seed_count=3,
        seed=42,
        dimension=2,
    )

    tasks = SyntheticTaskFamilyGenerator(family, scenario).generate()
    decisions, metrics = SimulationHarness(family).run(tasks)

    print("=" * 60)
    print("MOCKAPP Mathematical Approval - Stage 2 Simulation")
    print("=" * 60)
    print(format_metrics(metrics))
    print()
    print("Seed labels supplied to the mathematical engine: 3 approved")
    print("Live filesystem/browser integration: NONE")
    print()
    print("Sample decisions:")
    for decision in decisions[:10]:
        print(
            json.dumps(
                {
                    "task_id": decision.task_id,
                    "predicted": decision.predicted.value,
                    "truth": decision.ground_truth.value,
                    "density_ratio": round(decision.density_ratio, 6),
                    "log_density_ratio": round(decision.log_density_ratio, 6),
                    "pmf_probability": round(decision.pmf_probability, 6),
                    "near_saddle": decision.near_saddle,
                    "routed": decision.used_route_to_minimum,
                }
            )
        )


if __name__ == "__main__":
    main()
