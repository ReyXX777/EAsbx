from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

from .models import ActionObservation, ProbabilityEstimate


class PMFModel:
    """Bernoulli PMF estimator with a Beta prior.

    For binary human outcomes:
        P(approved) = (approved + alpha) /
                       (total + alpha + beta)

    The prior prevents two or three examples from producing artificial
    certainty.
    """

    def __init__(self, alpha: float = 1.0, beta: float = 1.0) -> None:
        if alpha <= 0 or beta <= 0:
            raise ValueError("Beta prior parameters must be positive.")
        self.alpha = float(alpha)
        self.beta = float(beta)

    def estimate(
        self, observations: Iterable[ActionObservation]
    ) -> ProbabilityEstimate:
        observations = list(observations)
        approved_weight = sum(o.weight for o in observations if o.approved)
        rejected_weight = sum(o.weight for o in observations if not o.approved)
        total_weight = approved_weight + rejected_weight

        probability = (approved_weight + self.alpha) / (
            total_weight + self.alpha + self.beta
        )

        return ProbabilityEstimate(
            probability=probability,
            sample_count=len(observations),
            effective_count=total_weight,
        )

    def pmf(self, probability: float, outcome: bool) -> float:
        p = min(max(float(probability), 0.0), 1.0)
        return p if outcome else 1.0 - p


class PDFModel:
    """Multivariate Gaussian PDF used as a similarity/density signal.

    This is deliberately a density signal, not an approval probability.
    A task near previously observed feature space receives higher density.
    """

    def __init__(self, regularization: float = 1e-6) -> None:
        if regularization <= 0:
            raise ValueError("regularization must be positive.")
        self.regularization = regularization

    def fit(
        self, vectors: list[tuple[float, ...]]
    ) -> tuple[tuple[float, ...], list[list[float]]]:
        if not vectors:
            raise ValueError("At least one vector is required.")

        dimension = len(vectors[0])
        if dimension == 0 or any(len(v) != dimension for v in vectors):
            raise ValueError("All vectors must have the same non-zero dimension.")

        n = len(vectors)
        mean = tuple(sum(v[d] for v in vectors) / n for d in range(dimension))

        covariance = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
        denominator = max(n - 1, 1)

        for v in vectors:
            delta = [v[d] - mean[d] for d in range(dimension)]
            for i in range(dimension):
                for j in range(dimension):
                    covariance[i][j] += delta[i] * delta[j] / denominator

        for i in range(dimension):
            covariance[i][i] += self.regularization

        return mean, covariance

    def density(
        self,
        vector: tuple[float, ...],
        mean: tuple[float, ...],
        covariance: list[list[float]],
    ) -> float:
        dimension = len(vector)
        if len(mean) != dimension or len(covariance) != dimension:
            raise ValueError("Dimension mismatch.")

        inv = _invert_matrix(covariance)
        delta = [vector[i] - mean[i] for i in range(dimension)]

        quadratic = 0.0
        for i in range(dimension):
            for j in range(dimension):
                quadratic += delta[i] * inv[i][j] * delta[j]

        determinant = _determinant(covariance)
        if determinant <= 0:
            raise ValueError("Covariance matrix must be positive definite.")

        normalization = math.sqrt(((2.0 * math.pi) ** dimension) * determinant)
        return math.exp(-0.5 * quadratic) / normalization

    def log_density(
        self,
        vector: tuple[float, ...],
        mean: tuple[float, ...],
        covariance: list[list[float]],
    ) -> float:
        dimension = len(vector)

        if len(mean) != dimension or len(covariance) != dimension:
            raise ValueError("Dimension mismatch.")

        inv = _invert_matrix(covariance)
        delta = [vector[i] - mean[i] for i in range(dimension)]

        quadratic = 0.0
        for i in range(dimension):
            for j in range(dimension):
                quadratic += delta[i] * inv[i][j] * delta[j]

        determinant = _determinant(covariance)

        if determinant <= 0:
            raise ValueError("Covariance matrix must be positive definite.")

        return (
            -0.5 * quadratic
            - 0.5 * dimension * math.log(2.0 * math.pi)
            - 0.5 * math.log(determinant)
        )


def _determinant(matrix: list[list[float]]) -> float:
    n = len(matrix)
    a = [row[:] for row in matrix]
    det = 1.0

    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(a[r][i]))
        if abs(a[pivot][i]) < 1e-12:
            return 0.0
        if pivot != i:
            a[i], a[pivot] = a[pivot], a[i]
            det *= -1

        pivot_value = a[i][i]
        det *= pivot_value

        for r in range(i + 1, n):
            factor = a[r][i] / pivot_value
            for c in range(i, n):
                a[r][c] -= factor * a[i][c]

    return det


def _invert_matrix(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)
    a = [
        row[:] + [1.0 if i == j else 0.0 for j in range(n)]
        for i, row in enumerate(matrix)
    ]

    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(a[r][i]))
        if abs(a[pivot][i]) < 1e-12:
            raise ValueError("Singular matrix.")

        a[i], a[pivot] = a[pivot], a[i]
        divisor = a[i][i]
        a[i] = [x / divisor for x in a[i]]

        for r in range(n):
            if r == i:
                continue
            factor = a[r][i]
            a[r] = [a[r][c] - factor * a[i][c] for c in range(2 * n)]

    return [row[n:] for row in a]
