# Stage 4 — Rejection-Aware Historical Boundary Learning

Stage 4 extends the standalone mathematical approval package with **three-way human history**:

- `ALLOW` — positive execution evidence.
- `DENY` — negative/safety-boundary evidence.
- `REVIEW` — uncertainty/boundary evidence.

The package remains independent from MOCKAPP's filesystem/browser code.

## Mathematical design

### 1. Categorical PMF

A Dirichlet-smoothed categorical PMF estimates historical base rates for ALLOW/REVIEW/DENY. It is a prior, not proof that a future task is safe.

### 2. Conditional PDFs

ALLOW and DENY observations are fitted as separate local Gaussian feature distributions. The decision engine compares:

`P(ALLOW | x) ∝ P(x | ALLOW) P(ALLOW)`

against

`P(DENY | x) ∝ P(x | DENY) P(DENY)`.

REVIEW observations are **not** added to the ALLOW density. They create a local review shell around known uncertain examples.

### 3. Jacobian/Hessian

The existing geometry layer remains advisory. A saddle condition suppresses automatic execution. A route toward the ALLOW basin is reported as geometry information only; it never converts a saddle directly into ALLOW.

## Experiments

The harness compares:

1. `2_allow_only`
2. `2_allow_1_deny`
3. `2_allow_1_review`
4. `2_allow_1_deny_1_review`

Each pattern is repeated with different random seeds. Metrics include accuracy, false-allow rate, false-deny rate, and review rate.

## Important interpretation

This stage does **not** establish production safety. It tests whether rejection and review history improves separation of synthetic safe/unsafe regions. In particular, false-allow rate is the safety-critical metric to inspect before any adapter is written.

## Run

```powershell
python -m pytest
python run_stage4.py
```

The next stage should only be considered after inspecting these results and adding more adversarial/OOD cases if the model appears overconfident.
