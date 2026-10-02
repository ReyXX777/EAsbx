from mathematical_approval.models import TaskFamily
from mathematical_approval.stage4 import Stage4HistoryHarness


if __name__ == "__main__":
    family = TaskFamily(
        key="read_table_calculate",
        description="Stable READ_TABLE -> CALCULATE task structure with changing values.",
    )
    report = Stage4HistoryHarness(family).repeated(repetitions=10, task_count=1000)

    print("Stage 4: three-label historical boundary experiment")
    print("=" * 72)
    for pattern in sorted({m.seed_pattern for m in report.metrics}):
        rows = [m for m in report.metrics if m.seed_pattern == pattern]
        print(f"\n{pattern}")
        print(f"  mean accuracy       : {sum(r.accuracy for r in rows)/len(rows):.4f}")
        print(f"  mean false-allow    : {sum(r.false_allow_rate for r in rows)/len(rows):.4f}")
        print(f"  mean false-deny     : {sum(r.false_deny_rate for r in rows)/len(rows):.4f}")
        print(f"  mean review rate    : {sum(r.review_rate for r in rows)/len(rows):.4f}")

    print("\n" + report.conclusion)
