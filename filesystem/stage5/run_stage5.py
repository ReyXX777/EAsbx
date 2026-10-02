from mathematical_approval import FeatureSpec, TaskFamilyDomain, DomainOODDetector, RepresentationSafetyGate

domain = TaskFamilyDomain.from_specs(
    "filesystem.read_table.calculate",
    [
        FeatureSpec("rows", minimum=1, maximum=2000),
        FeatureSpec("columns", minimum=1, maximum=50),
        FeatureSpec("numeric_ratio", minimum=0.0, maximum=1.0),
    ],
)
gate = RepresentationSafetyGate(domain, DomainOODDetector(3.0))

cases = {
    "normal": {"rows": 1000, "columns": 10, "numeric_ratio": 0.8},
    "boundary": {"rows": 1999, "columns": 49, "numeric_ratio": 0.99},
    "hard_ood": {"rows": 100000, "columns": 10, "numeric_ratio": 0.8},
}

for name, features in cases.items():
    result = gate.assess(features)
    print(f"{name}: {result.decision} | distance={result.ood.score:.3f} | reasons={result.ood.reasons}")
