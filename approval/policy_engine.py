from __future__ import annotations

from .models import (
    ApprovalDecision,
    ApprovalStatus,
    TaskClassification,
)


class ApprovalPolicyEngine:
    """
    Deterministic authorization policy.

    This class does not call Gemini and does not inspect browser state.
    """

    def evaluate(
        self,
        classification: TaskClassification,
    ) -> ApprovalDecision:

        reasons: list[str] = []

        # ---------------------------------------------------------
        # DENY
        # ---------------------------------------------------------

        if classification.destructive:
            reasons.append(
                "The task contains a destructive operation."
            )

            return ApprovalDecision(
                status=ApprovalStatus.DENY,
                classification=classification,
                reasons=tuple(reasons),
            )

        # ---------------------------------------------------------
        # HUMAN REVIEW
        # ---------------------------------------------------------

        if classification.credential_use:
            reasons.append(
                "The task requires credential use."
            )

        if classification.external_side_effect:
            reasons.append(
                "The task can cause an external side effect."
            )

        if classification.data_sensitivity in {
            "sensitive",
            "financial",
            "personal",
            "private",
            "authentication",
        }:
            reasons.append(
                "The task accesses sensitive information."
            )

        if reasons:
            return ApprovalDecision(
                status=ApprovalStatus.REVIEW,
                classification=classification,
                reasons=tuple(reasons),
            )

        # ---------------------------------------------------------
        # ALLOW
        # ---------------------------------------------------------

        reasons.append(
            "The task is classified as a non-destructive "
            "operation without sensitive access or external side effects."
        )

        return ApprovalDecision(
            status=ApprovalStatus.ALLOW,
            classification=classification,
            reasons=tuple(reasons),
        )