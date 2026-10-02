from mathematical_approval.models import TaskFamily, DecisionLabel
from mathematical_approval.simulation_metrics import summarize
from mathematical_approval.simulation_models import GroundTruth, SimulationDecision
from mathematical_approval.simulation_runner import SimulationHarness
from mathematical_approval.simulation_scenarios import ScenarioConfig, SyntheticTaskFamilyGenerator


def test_generator_produces_requested_count_and_three_seeds():
    family = TaskFamily("demo")
    tasks = SyntheticTaskFamilyGenerator(
        family,
        ScenarioConfig(task_count=100, seed_count=3, seed=1),
    ).generate()

    assert len(tasks) == 100
    assert sum(t.region == "approved_seed" for t in tasks) == 3
    assert all(t.family.key == "demo" for t in tasks)


def test_stage2_does_not_return_a_decision_for_seed_labels():
    family = TaskFamily("demo")
    tasks = SyntheticTaskFamilyGenerator(
        family,
        ScenarioConfig(task_count=20, seed_count=3, seed=2),
    ).generate()
    decisions, metrics = SimulationHarness(family).run(tasks)

    assert len(decisions) == 17
    assert metrics.total == 17


def test_metrics_count_false_allow_and_false_deny():
    family = TaskFamily("demo")
    decisions = [
        SimulationDecision(1, DecisionLabel.ALLOW, GroundTruth.APPROVED, 1, .9, 1, 1, 5, 5, 0, 0, False, False),
        SimulationDecision(2, DecisionLabel.ALLOW, GroundTruth.UNSAFE, 1, .9, 1, 1, 5, 5, 0, 0, False, False),
        SimulationDecision(3, DecisionLabel.DENY, GroundTruth.UNSAFE, 1, .1, 1, 1, .1, -2, 0, 0, False, False),
        SimulationDecision(4, DecisionLabel.DENY, GroundTruth.APPROVED, 1, .1, 1, 1, .1, -2, 0, 0, False, False),
    ]
    metrics = summarize(decisions)

    assert metrics.false_positive == 1
    assert metrics.false_negative == 1
    assert metrics.false_allow_rate == 0.5
    assert metrics.false_deny_rate == 0.5
