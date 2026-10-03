from task_observation_engine.mathematical_approval.geometry import (
    JacobianModel,
    HessianModel,
)
from task_observation_engine.mathematical_approval.models import FeatureVector


def bowl(x):
    return x[0] ** 2 + 3.0 * x[1] ** 2


def saddle(x):
    return x[0] ** 2 - x[1] ** 2


def test_jacobian_near_origin():
    gradient = JacobianModel().gradient(bowl, FeatureVector((0.0, 0.0)))
    assert abs(gradient[0]) < 1e-4
    assert abs(gradient[1]) < 1e-4


def test_bowl_is_not_saddle():
    h = HessianModel()
    matrix = h.hessian(bowl, FeatureVector((0.0, 0.0)))
    _, is_saddle = h.classify_curvature(matrix)
    assert not is_saddle


def test_saddle_is_detected():
    h = HessianModel()
    matrix = h.hessian(saddle, FeatureVector((0.0, 0.0)))
    _, is_saddle = h.classify_curvature(matrix)
    assert is_saddle
