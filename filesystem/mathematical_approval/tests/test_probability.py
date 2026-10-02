from mathematical_approval.models import ActionObservation, FeatureVector, TaskFamily, TaskHistory
from mathematical_approval.probability import PMFModel, PDFModel


def test_pmf_beta_prior():
    family = TaskFamily("test")
    history = TaskHistory()
    for _ in range(3):
        history.add(ActionObservation(family, FeatureVector((1.0,)), True))

    estimate = PMFModel().estimate(history.observations)
    assert estimate.probability == 0.8


def test_pdf_is_positive():
    model = PDFModel()
    mean, covariance = model.fit([(0.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    density = model.density((0.2, 0.2), mean, covariance)
    assert density > 0
