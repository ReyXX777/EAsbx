# Stage 3 — Stress Experiments

Stage 3 does **not** connect to MOCKAPP filesystem/browser execution.

## Purpose

Stress the mathematical approval hypothesis against:

1. IID variations
2. distribution drift
3. out-of-distribution values
4. adversarial values near the learned approved region
5. boundary cases
6. explicit Hessian saddle points
7. repeated random seeds with only 2 vs 3 approved examples

## Critical correction from Stage 2

The Stage 2 simulator used hidden unsafe examples to construct an unsafe PDF. That is useful as an oracle experiment, but it leaks evaluation labels into the classifier.

Stage 3's production-like harness does **not** fit an unsafe PDF. It only sees the approved seed examples. Ground truth is retained exclusively for measuring the result after prediction.

This distinction is essential before claiming that the mathematical model generalizes.

## Saddle behavior

A deliberate objective `f(x,y)=x²-y²` has Hessian eigenvalues `(+2,-2)`, making the saddle region unambiguous. Stage 3 verifies that saddle points are never converted into automatic ALLOW merely because a route toward the approved basin exists.

Routing is therefore advisory: reaching a known approved basin does not itself authorize execution.

## Running

From the mathematical package root:

```powershell
python run_stage3.py
```

Run tests:

```powershell
pytest -q
```

## Interpretation

The most important Stage 3 metrics are:

- false-allow rate
- false-deny rate
- review rate
- performance under distribution drift
- adversarial false allows
- saddle suppression
- variance across random seeds

High accuracy alone is insufficient for a safety approval system. In particular, a model that obtains high accuracy by allowing unsafe tasks is unacceptable.
