from mathematical_approval.history import LabeledObservation, LabeledTaskHistory
from mathematical_approval.models import DecisionLabel, FeatureVector, TaskFamily


def test_review_is_preserved_as_its_own_label():
    family = TaskFamily("read_table_calculate")
    history = LabeledTaskHistory()
    history.add(LabeledObservation(family, FeatureVector((0.0, 0.0)), DecisionLabel.ALLOW))
    history.add(LabeledObservation(family, FeatureVector((1.0, 1.0)), DecisionLabel.REVIEW))
    history.add(LabeledObservation(family, FeatureVector((3.0, 3.0)), DecisionLabel.DENY))

    assert history.count(family, DecisionLabel.ALLOW) == 1
    assert history.count(family, DecisionLabel.REVIEW) == 1
    assert history.count(family, DecisionLabel.DENY) == 1
