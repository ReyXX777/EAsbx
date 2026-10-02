from mathematical_approval import (
    FeatureSpec, TaskFamilyDomain, DomainOODDetector, RepresentationSafetyGate
)


def make_gate():
    domain = TaskFamilyDomain.from_specs(
        "filesystem.read_table.calculate",
        [
            FeatureSpec("rows", minimum=1, maximum=2000),
            FeatureSpec("columns", minimum=1, maximum=50),
            FeatureSpec("numeric_ratio", minimum=0.0, maximum=1.0),
        ],
    )
    return RepresentationSafetyGate(domain, DomainOODDetector(distance_threshold=3.0))


def test_normalizes_named_features():
    result = make_gate().assess({"rows": 1000, "columns": 10, "numeric_ratio": 0.8})
    assert result.decision == "IN_DOMAIN"
    assert not result.ood.is_ood


def test_hard_domain_violation_is_review():
    result = make_gate().assess({"rows": 100000, "columns": 10, "numeric_ratio": 0.8})
    assert result.decision == "REVIEW"
    assert result.ood.is_ood


def test_distance_can_trigger_ood_inside_bounds():
    # Use a separate domain whose statistical center is narrower than its
    # hard bounds, so distance-based OOD is independently exercised.
    from mathematical_approval import FeatureNormalizer
    domain = TaskFamilyDomain.from_specs(
        "distance-test",
        [
            FeatureSpec("rows", minimum=1, maximum=2000, center=1000, scale=100),
            FeatureSpec("columns", minimum=1, maximum=50, center=10, scale=5),
            FeatureSpec("numeric_ratio", minimum=0.0, maximum=1.0, center=0.5, scale=0.1),
        ],
    )
    result = RepresentationSafetyGate(domain, DomainOODDetector(3.0)).assess(
        {"rows": 1300, "columns": 20, "numeric_ratio": 0.8}
    )
    assert result.decision == "REVIEW"


def test_missing_feature_fails_closed():
    import pytest
    with pytest.raises(ValueError):
        make_gate().assess({"rows": 10, "columns": 4})


def test_representation_is_named_and_ordered():
    normalized = make_gate().domain.normalize(
        {"numeric_ratio": 0.5, "columns": 5, "rows": 100}
    )
    assert normalized.names == ("rows", "columns", "numeric_ratio")
    assert normalized.family == "filesystem.read_table.calculate"
