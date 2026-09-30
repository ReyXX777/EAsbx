from __future__ import annotations

from approval.models import (
    ApprovalDecision,
    ApprovalResult,
    JevDecision,
    RiskLevel,
    TaskRequest,
)


class ApprovalPolicy:
    """
    Deterministic authorization policy.

    JEV provides a decision signal.
    This policy owns the final authorization boundary.
    """

    def evaluate(
        self,
        task: TaskRequest,
        jev: JevDecision,
    ) -> ApprovalResult:

        # Critical operations always require a human.
        if task.risk_level == RiskLevel.CRITICAL:

            return ApprovalResult(
                decision=ApprovalDecision.REQUIRE_APPROVAL,
                reason_code=(
                    "critical_operation_requires_human"
                ),
                requires_human=True,
                risk_level=task.risk_level,
                confidence=jev.confidence,
            )

        # High-risk operations always require approval
        # in this prototype.
        if task.risk_level == RiskLevel.HIGH:

            return ApprovalResult(
                decision=ApprovalDecision.REQUIRE_APPROVAL,
                reason_code=(
                    "high_risk_operation_requires_human"
                ),
                requires_human=True,
                risk_level=task.risk_level,
                confidence=jev.confidence,
            )

        # JEV can explicitly deny a lower-risk task.
        if jev.decision == ApprovalDecision.DENY:

            return ApprovalResult(
                decision=ApprovalDecision.DENY,
                reason_code="jev_denied",
                requires_human=False,
                risk_level=task.risk_level,
                confidence=jev.confidence,
            )

        # Medium-risk tasks require approval if JEV
        # does not explicitly allow them.
        if task.risk_level == RiskLevel.MEDIUM:

            if (
                jev.decision
                != ApprovalDecision.ALLOW
            ):
                return ApprovalResult(
                    decision=(
                        ApprovalDecision.REQUIRE_APPROVAL
                    ),
                    reason_code=(
                        "medium_risk_not_explicitly_allowed"
                    ),
                    requires_human=True,
                    risk_level=task.risk_level,
                    confidence=jev.confidence,
                )

        # Low-risk task explicitly allowed.
        return ApprovalResult(
            decision=ApprovalDecision.ALLOW,
            reason_code="low_risk_allowed",
            requires_human=False,
            risk_level=task.risk_level,
            confidence=jev.confidence,
        )