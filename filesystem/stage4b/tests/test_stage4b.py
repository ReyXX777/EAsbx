from mathematical_approval.models import TaskFamily
from mathematical_approval.stage4b import (
    Stage4BScenario,
    Stage4BStressHarness,
    StressCase,
)


def family():
    return TaskFamily("read_table_calculate")


def test_stage4b_all_cases_are_deterministic_and_bounded():
    harness = Stage4BStressHarness(family())
    for case in StressCase:
        result = harness.run(Stage4BScenario(case, "2_allow_1_deny", 123, 200))
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.false_allow_rate <= 1.0
        assert 0.0 <= result.review_rate <= 1.0
        assert 0.0 <= result.automatic_coverage <= 1.0


def test_saddle_cases_never_auto_allow():
    harness = Stage4BStressHarness(family())
    result = harness.run(Stage4BScenario(StressCase.SADDLE, "2_allow_1_deny", 7, 100))
    assert result.saddle_review_rate == 1.0
    assert result.false_allow_rate == 0.0


def test_ood_cases_are_not_automatically_allowed():
    harness = Stage4BStressHarness(family())
    result = harness.run(Stage4BScenario(StressCase.OOD, "2_allow_1_deny", 8, 100))
    assert result.ood_false_allow_rate > 0.0


def test_adversarial_cases_expose_safe_density_weakness_if_present():
    harness = Stage4BStressHarness(family())
    result = harness.run(Stage4BScenario(StressCase.ADVERSARIAL, "2_allow_1_deny", 9, 200))
    assert 0.0 <= result.adversarial_false_allow_rate <= 1.0


def test_three_allow_two_deny_history_is_supported():
    harness = Stage4BStressHarness(family())
    result = harness.run(Stage4BScenario(StressCase.IID, "3_allow_2_deny", 10, 100))
    assert result.total == 100
