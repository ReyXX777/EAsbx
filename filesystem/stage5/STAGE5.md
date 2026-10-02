# Stage 5 — Feature Normalization, Representation, and OOD Gate

Stage 5 adds a deliberately independent representation layer before PMF/PDF/Jacobian/Hessian approval logic.

Pipeline:

Task
-> canonical feature extraction
-> FeatureNormalizer
-> TaskFamilyDomain
-> DomainOODDetector
-> REVIEW on OOD
-> only then statistical/geometric approval

## Design rules

1. Features are named and ordered deterministically.
2. Raw values are never compared directly when their scales differ.
3. Every task family declares an operating domain.
4. Explicit hard-bound violations are OOD.
5. Excessive normalized distance is OOD.
6. OOD is `REVIEW`, never automatic `ALLOW`.
7. This package does not call filesystem code.
8. The adapter can later provide a mapping from a filesystem operation into this feature contract.

## Important limitation

Stage 5 is a representation/domain safety gate, not a learned OOD detector. The domain bounds are currently explicit. Later experiments can learn robust centers/scales and empirical support regions from history, but an empirical model must remain fail-closed.

## Suggested next stage

Stage 6 should connect Stage 5 to the existing history-aware mathematical engine *inside the mathematical package only*, producing:

IN_DOMAIN -> PMF/PDF/Jacobian/Hessian decision
OOD       -> REVIEW

The filesystem adapter should remain untouched until that combined model survives hostile simulation.
