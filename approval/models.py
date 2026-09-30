from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskKind(str, Enum):
    """
    High-level capability involved in a task.
    """

    BROWSER = "browser"
    FILESYSTEM = "filesystem"
    OTHER = "other"


class RiskLevel(str, Enum):
    """
    Application-level risk classification.

    This is deliberately independent from JEV.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalDecision(str, Enum):
    """
    Final authorization decision made by our application.
    """

    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True)
class TaskRequest:
    """
    Normalized representation of a task entering the approval layer.

    This object contains no Qt or browser-use objects.
    """

    prompt: str
    kind: TaskKind

    target: str | None = None
    requested_action: str | None = None

    risk_level: RiskLevel = RiskLevel.LOW

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class JevDecision:
    """
    Raw normalized decision returned by the JEV adapter.

    JEV-specific response objects never escape jev_client.py.
    """

    decision: ApprovalDecision
    confidence: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class ApprovalResult:
    """
    Final application-level authorization result.
    """

    decision: ApprovalDecision

    reason_code: str

    requires_human: bool

    risk_level: RiskLevel

    confidence: float | None = None

    source: str = "policy"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def allowed(self) -> bool:
        return (
            self.decision
            == ApprovalDecision.ALLOW
        )