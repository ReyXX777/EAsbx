from mathematical_approval.models import DecisionLabel, TaskFamily, FeatureVector
from mathematical_approval.history import LabeledTaskHistory, LabeledObservation
from mathematical_approval.stage4 import HistoryAwareApprovalEngine, Stage4HistoryHarness


def test_requires_both_allow_and_deny_history_for_automatic_decision():
    family = TaskFamily("read_table_calculate")
    history = LabeledTaskHistory()
    history.add(LabeledObservation(family, FeatureVector((0.0, 0.0)), DecisionLabel.ALLOW))
    history.add(LabeledObservation(family, FeatureVector((0.1, 0.1)), DecisionLabel.ALLOW))

    engine = HistoryAwareApprovalEngine(min_class_samples=2)
    label, details = engine.decide(history, family, FeatureVector((0.0, 0.0)))

    assert label == DecisionLabel.REVIEW
    assert "ALLOW and DENY" in details["reason"]


def test_deny_history_changes_unsafe_region():
    family = TaskFamily("read_table_calculate")
    history = LabeledTaskHistory()
    history.add(LabeledObservation(family, FeatureVector((0.0, 0.0)), DecisionLabel.ALLOW))
    history.add(LabeledObservation(family, FeatureVector((0.1, 0.0)), DecisionLabel.ALLOW))
    history.add(LabeledObservation(family, FeatureVector((3.0, 3.0)), DecisionLabel.DENY))
    history.add(LabeledObservation(family, FeatureVector((3.1, 3.0)), DecisionLabel.DENY))

    engine = HistoryAwareApprovalEngine(min_class_samples=2)
    label, _ = engine.decide(history, family, FeatureVector((3.0, 3.0)))
    assert label == DecisionLabel.DENY


def test_review_history_creates_boundary_review():
    family = TaskFamily("read_table_calculate")
    history = LabeledTaskHistory()
    history.add(LabeledObservation(family, FeatureVector((0.0, 0.0)), DecisionLabel.ALLOW))
    history.add(LabeledObservation(family, FeatureVector((0.1, 0.0)), DecisionLabel.ALLOW))
    history.add(LabeledObservation(family, FeatureVector((3.0, 3.0)), DecisionLabel.DENY))
    history.add(LabeledObservation(family, FeatureVector((3.1, 3.0)), DecisionLabel.DENY))
    history.add(LabeledObservation(family, FeatureVector((1.4, 1.4)), DecisionLabel.REVIEW))

    engine = HistoryAwareApprovalEngine(min_class_samples=2, review_radius=0.75)
    label, _ = engine.decide(history, family, FeatureVector((1.4, 1.4)))
    assert label == DecisionLabel.REVIEW


def test_harness_runs_all_history_patterns():
    report = Stage4HistoryHarness(TaskFamily("read_table_calculate")).repeated(repetitions=2, task_count=100)
    assert len(report.metrics) == 8
    assert 0.0 <= report.mean_accuracy <= 1.0
