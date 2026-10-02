from mathematical_approval.models import TaskFamily
from mathematical_approval.stage4b import Stage4BStressHarness, StressCase


if __name__ == "__main__":
    family = TaskFamily(
        key="read_table_calculate",
        description="Stable READ_TABLE -> CALCULATE task structure with changing values.",
    )
    report = Stage4BStressHarness(family).repeated(repetitions=10, task_count=1000)

    print("Stage 4B: hostile history / distribution stress experiment")
    print("=" * 88)
    for case in StressCase:
        rows = [m for m in report.metrics if m.case == case.value]
        print(f"\n[{case.value}]")
        for pattern in sorted({m.history_pattern for m in rows}):
            group = [m for m in rows if m.history_pattern == pattern]
            print(f"  {pattern}")
            print(f"    accuracy                 : {sum(x.accuracy for x in group)/len(group):.4f}")
            print(f"    false-allow              : {sum(x.false_allow_rate for x in group)/len(group):.4f}")
            print(f"    false-deny               : {sum(x.false_deny_rate for x in group)/len(group):.4f}")
            print(f"    review-rate              : {sum(x.review_rate for x in group)/len(group):.4f}")
            print(f"    automatic-coverage       : {sum(x.automatic_coverage for x in group)/len(group):.4f}")
            print(f"    conditional-accuracy     : {sum(x.conditional_accuracy for x in group)/len(group):.4f}")
            print(f"    adversarial false-allow  : {sum(x.adversarial_false_allow_rate for x in group)/len(group):.4f}")
            print(f"    OOD false-allow          : {sum(x.ood_false_allow_rate for x in group)/len(group):.4f}")
            print(f"    boundary review          : {sum(x.boundary_review_rate for x in group)/len(group):.4f}")
            print(f"    saddle review            : {sum(x.saddle_review_rate for x in group)/len(group):.4f}")

    print("\nOverall")
    print(f"  mean accuracy             : {report.mean_accuracy:.4f}")
    print(f"  accuracy stddev           : {report.stddev_accuracy:.4f}")
    print(f"  mean false-allow          : {report.mean_false_allow_rate:.4f}")
    print(f"  worst false-allow         : {report.worst_false_allow_rate:.4f}")
    print(f"  mean review-rate          : {report.mean_review_rate:.4f}")
    print(f"\n{report.conclusion}")
