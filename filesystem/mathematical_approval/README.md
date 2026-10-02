# Mathematical Approval — Stage 1

Standalone mathematical decision package for MOCKAPP.

## Goal

This package investigates whether repeated task families can produce useful
approval signals from a small amount of manually labelled history.

It currently contains:

- PMF: Bayesian Bernoulli approval estimate.
- PDF: Gaussian feature-space density signal.
- Jacobian: numerical local sensitivity/gradient.
- Hessian: numerical local curvature.
- Saddle detection for mixed-sign Hessian eigenvalues.
- Confidence adjustment based on effective historical sample count.
- A conservative `ALLOW / REVIEW / DENY` decision API.
- Deterministic simulation helpers.
- Unit tests.

## Important architectural rule

There is **no import from MOCKAPP filesystem code**.

A future adapter should look conceptually like:

    filesystem task
          |
          v
    feature extractor
          |
          v
    mathematical_approval API
          |
          v
    decision signal
          |
          v
    existing ApprovalEngine / policy layer

The mathematical package should not directly execute, approve, deny, delete,
write, move, copy, browse, or otherwise perform an operation.

## Why Stage 1 is conservative

Two or three manually approved examples are not enough to establish a
high-confidence automatic policy by themselves. The package therefore keeps
sample count and confidence explicit and can require REVIEW until sufficient
history exists.

The PDF is treated as a density/similarity signal, not as an approval
probability. Jacobian/Hessian values are treated as local geometry signals,
not as proof of safety.

## Install/test

From the package directory:

    python -m pytest

Demo:

    python -m mathematical_approval.simulation
