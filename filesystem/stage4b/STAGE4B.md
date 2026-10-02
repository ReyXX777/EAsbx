# Stage 4B — Hostile History and Distribution Stress

Stage 4B evaluates the Stage 4 history-aware approval engine without connecting it to MOCKAPP.

## What is stressed

- IID safe/unsafe regions
- multiple unseen safe and unsafe clusters
- distribution drift
- extreme out-of-distribution (OOD) values
- adversarial unsafe points close to the learned safe basin
- boundary points
- deliberately misleading DENY history
- explicit Hessian saddle cases
- feature-scale drift
- 2 ALLOW + 1 DENY versus 3 ALLOW + 2 DENY histories
- repeated random seeds

## Important evaluation rule

The hidden ground-truth label is used only to calculate metrics. It is never added to the history during evaluation.

## Safety interpretation

A low false-allow rate is necessary but not sufficient for production approval. In particular, a Gaussian PDF can assign high density to an unsafe point that happens to be close to safe historical points. Stage 4B deliberately measures this failure mode instead of hiding it.

Saddle routing remains advisory. A route toward a safe basin must never itself authorize an operation.

## Run

```powershell
cd X:\MOCKAPP\filesystem\mathematical_approval
python run_stage4b.py
```

or:

```powershell
python -m pytest -q
```

The experiment is research-only and must pass before any filesystem adapter is connected.
