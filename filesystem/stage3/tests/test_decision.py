from mathematical_approval.decision import MathematicalApprovalEngine
from mathematical_approval.models import ActionObservation, FeatureVector, TaskFamily, TaskHistory, DecisionLabel


def test_sparse_history_requires_review():
    family = TaskFamily("filesystem.read_table.calculate")
    history = TaskHistory()

    for _ in range(3):
        history.add(
            ActionObservation(
                family,
                FeatureVector((1.0, 1.0)),
                approved=True,
            )
        )

    engine = MathematicalApprovalEngine(min_samples_for_automatic=10)
    decision = engine.decide(history, family, FeatureVector((1.0, 1.0)))

    assert decision.label == DecisionLabel.REVIEW


def test_mature_high_approval_history_can_allow():
    family = TaskFamily("filesystem.read_table.calculate")
    history = TaskHistory()

    for _ in range(100):
        history.add(
            ActionObservation(
                family,
                FeatureVector((1.0, 1.0)),
                approved=True,
            )
        )

    for _ in range(1):
        history.add(
            ActionObservation(
                family,
                FeatureVector((1.0, 1.0)),
                approved=False,
            )
        )

    engine = MathematicalApprovalEngine(min_samples_for_automatic=10)
    decision = engine.decide(history, family, FeatureVector((1.0, 1.0)))

    assert decision.label == DecisionLabel.ALLOW
