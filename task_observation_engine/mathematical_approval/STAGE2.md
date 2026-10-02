# Stage 2 — Simulation Harness + Experiments

This stage is deliberately isolated from MOCKAPP execution.

## Experiment

The default experiment models one recurring task family:

`filesystem.read_table.calculate`

The task structure stays fixed while numeric feature values vary across 1,000 synthetic sessions.
Only three initial examples are supplied as human-approved seed observations.

The simulator evaluates:

- PMF: historical approval prior.
- PDF: density of the candidate relative to approved and hidden unsafe reference regions.
- Jacobian: local sensitivity signal.
- Hessian: local curvature / saddle signal.
- Route-to-minimum: an offline gradient-style route toward the approved basin when the synthetic geometry enters the saddle region.

## Important limitation

The simulator's unsafe reference distribution is **synthetic ground truth**. It is not available to a real approval adapter. Therefore a good Stage 2 result does not prove production safety; it only tells us whether the mathematical design is capable of separating the constructed regions.

A particularly important failure mode is PMF-only approval: if all three seed examples are approved, a PMF can remain high even when a new task is far outside the known safe feature region. The harness therefore treats PMF as a prior rather than a sufficient approval signal.

## Run

From this directory:

```powershell
python run_stage2.py
```

Run tests:

```powershell
pytest -q
```

## What to record

For every experiment record:

- false-allow rate — unsafe tasks automatically allowed;
- false-deny rate — safe tasks automatically denied;
- review rate — tasks that remain uncertain;
- accuracy;
- behavior near the synthetic boundary;
- behavior at the saddle region;
- sensitivity to only 2 vs 3 seed labels;
- sensitivity to distribution drift.

The next experiment should vary the data distribution rather than immediately connecting this package to the filesystem agent.
