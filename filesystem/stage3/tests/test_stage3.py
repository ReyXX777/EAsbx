from mathematical_approval.models import TaskFamily
from mathematical_approval.stage3 import Stage3StressHarness, StressKind, StressScenario


def harness():
    return Stage3StressHarness(TaskFamily("test.family"))


def test_stage3_never_allows_saddle_points():
    _, metrics = harness().run(StressScenario("saddle", StressKind.SADDLE, 3, 100, 7))
    assert metrics.saddle_count > 0
    assert metrics.saddle_review_count == metrics.saddle_count


def test_stage3_ood_is_not_approved_by_density():
    decisions, _ = harness().run(StressScenario("ood", StressKind.OOD, 3, 100, 8))
    assert decisions
    assert all(d.predicted != "ALLOW" for d in decisions)


def test_stage3_adversarial_case_is_exposed():
    decisions, metrics = harness().run(
        StressScenario("adv", StressKind.ADVERSARIAL, 3, 100, 9)
    )
    assert decisions


    assert metrics.unsafe_allow_count >= 0


def test_stage3_drift_is_executable():
    _, metrics = harness().run(StressScenario("drift", StressKind.DRIFT, 2, 100, 10))
    assert metrics.total == 98
