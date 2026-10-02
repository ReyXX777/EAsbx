from __future__ import annotations

from collections import defaultdict

from mathematical_approval.models import TaskFamily
from mathematical_approval.stage3 import Stage3StressHarness, StressKind, StressScenario


def main() -> None:
    family = TaskFamily(
        key="filesystem.read_table.calculate",
        description="Stable READ_TABLE -> CALCULATE structure with changing values.",
    )
    harness = Stage3StressHarness(family)

    print("=" * 72)
    print("MOCKAPP Mathematical Approval - Stage 3 Stress Experiments")
    print("=" * 72)
    print("Production-like mode: classifier sees approved seeds only.")
    print("Unsafe labels are hidden until evaluation.")
    print()

    for kind in StressKind:
        for seed_count in (2, 3):
            scenario = StressScenario(
                name=f"{kind.value}-seed{seed_count}",
                kind=kind,
                seed_count=seed_count,
                task_count=1000,
                seed=42,
            )
            _, metrics = harness.run(scenario)
            print(
                f"{kind.value:24} seeds={seed_count} "
                f"accuracy={metrics.accuracy:.3f} "
                f"false_allow={metrics.false_allow_rate:.3f} "
                f"false_deny={metrics.false_deny_rate:.3f} "
                f"review={metrics.review_rate:.3f} "
                f"coverage={metrics.automatic_coverage:.3f} "
                f"conditional_acc={metrics.conditional_accuracy:.3f} "
                f"safe_auto={metrics.safe_automation_rate:.3f} "
                f"saddles={metrics.saddle_count}"
            )

    print()
    print("Repeated IID experiment: 25 random seeds for both 2 and 3 labels")
    report = harness.repeated_seed_experiment(
        kind=StressKind.IID,
        seed_counts=(2, 3),
        repetitions=25,
        task_count=1000,
    )
    print(f"Mean accuracy:       {report.repeated_seed_accuracy_mean:.4f}")
    print(f"Accuracy stddev:     {report.repeated_seed_accuracy_stddev:.4f}")
    print(f"Mean false-allow:    {report.repeated_seed_false_allow_mean:.4f}")
    print(report.production_like_note)


if __name__ == "__main__":
    main()
