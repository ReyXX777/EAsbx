from __future__ import annotations

import math
from collections.abc import Callable

from .models import FeatureVector, GeometryEstimate


ScalarFunction = Callable[[tuple[float, ...]], float]


class JacobianModel:
    """Finite-difference Jacobian/gradient estimator.

    Stage 1 uses numerical differentiation so the mathematical package does
    not require callers to provide symbolic derivatives.
    """

    def __init__(self, epsilon: float = 1e-5) -> None:
        if epsilon <= 0:
            raise ValueError("epsilon must be positive.")
        self.epsilon = epsilon

    def gradient(self, function: ScalarFunction, point: FeatureVector) -> tuple[float, ...]:
        x = list(point.values)
        result = []

        for i in range(len(x)):
            plus = x[:]
            minus = x[:]
            plus[i] += self.epsilon
            minus[i] -= self.epsilon
            result.append(
                (function(tuple(plus)) - function(tuple(minus)))
                / (2.0 * self.epsilon)
            )

        return tuple(result)

    def norm(self, gradient: tuple[float, ...]) -> float:
        return math.sqrt(sum(x * x for x in gradient))


class HessianModel:
    """Finite-difference Hessian estimator and local curvature classifier."""

    def __init__(self, epsilon: float = 1e-4) -> None:
        if epsilon <= 0:
            raise ValueError("epsilon must be positive.")
        self.epsilon = epsilon

    def hessian(
        self,
        function: ScalarFunction,
        point: FeatureVector,
    ) -> list[list[float]]:
        x = list(point.values)
        n = len(x)
        h = self.epsilon
        matrix = [[0.0] * n for _ in range(n)]

        f0 = function(tuple(x))

        for i in range(n):
            plus = x[:]
            minus = x[:]
            plus[i] += h
            minus[i] -= h
            matrix[i][i] = (
                function(tuple(plus))
                - 2.0 * f0
                + function(tuple(minus))
            ) / (h * h)

            for j in range(i + 1, n):
                pp = x[:]
                pm = x[:]
                mp = x[:]
                mm = x[:]

                pp[i] += h; pp[j] += h
                pm[i] += h; pm[j] -= h
                mp[i] -= h; mp[j] += h
                mm[i] -= h; mm[j] -= h

                value = (
                    function(tuple(pp))
                    - function(tuple(pm))
                    - function(tuple(mp))
                    + function(tuple(mm))
                ) / (4.0 * h * h)

                matrix[i][j] = value
                matrix[j][i] = value

        return matrix

    def eigenvalues(self, matrix: list[list[float]]) -> list[float]:
        """Jacobi eigenvalue algorithm for small symmetric Hessians."""
        a = [row[:] for row in matrix]
        n = len(a)

        for _ in range(max(20, 10 * n * n)):
            p, q = 0, 0
            largest = 0.0

            for i in range(n):
                for j in range(i + 1, n):
                    if abs(a[i][j]) > largest:
                        largest = abs(a[i][j])
                        p, q = i, j

            if largest < 1e-10:
                break

            angle = 0.5 * math.atan2(
                2.0 * a[p][q],
                a[q][q] - a[p][p],
            )
            c = math.cos(angle)
            s = math.sin(angle)

            for k in range(n):
                if k != p and k != q:
                    apk = a[p][k]
                    aqk = a[q][k]
                    a[p][k] = a[k][p] = c * apk - s * aqk
                    a[q][k] = a[k][q] = s * apk + c * aqk

            app = a[p][p]
            aqq = a[q][q]
            apq = a[p][q]

            a[p][p] = c*c*app - 2*s*c*apq + s*s*aqq
            a[q][q] = s*s*app + 2*s*c*apq + c*c*aqq
            a[p][q] = a[q][p] = 0.0

        return [a[i][i] for i in range(n)]

    def classify_curvature(self, hessian: list[list[float]], tolerance: float = 1e-6) -> tuple[float, bool]:
        eigenvalues = self.eigenvalues(hessian)
        curvature = max(abs(x) for x in eigenvalues) if eigenvalues else 0.0
        has_positive = any(x > tolerance for x in eigenvalues)
        has_negative = any(x < -tolerance for x in eigenvalues)
        near_saddle = has_positive and has_negative
        return curvature, near_saddle


def build_geometry_estimate(
    function: ScalarFunction,
    point: FeatureVector,
    jacobian: JacobianModel,
    hessian: HessianModel,
) -> GeometryEstimate:
    gradient = jacobian.gradient(function, point)
    matrix = hessian.hessian(function, point)
    curvature, near_saddle = hessian.classify_curvature(matrix)

    hessian_norm = math.sqrt(
        sum(value * value for row in matrix for value in row)
    )

    return GeometryEstimate(
        gradient_norm=jacobian.norm(gradient),
        jacobian_norm=jacobian.norm(gradient),
        hessian_norm=hessian_norm,
        curvature=curvature,
        condition_indicator=1.0 / (1.0 + hessian_norm),
        near_saddle=near_saddle,
    )
