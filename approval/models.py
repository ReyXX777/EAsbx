from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ApprovalStatus(str, Enum):
    """
    Final authorization state produced by the local policy engine.
    """

    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


@dataclass(frozen=True)
class TaskClassification:
    """
    Structured facts about what a task is asking the agent to do.

    This object contains classification facts only.
    It does not decide whether the task should execute.
    """

    operation_type: str
    data_sensitivity: str
    external_side_effect: bool
    destructive: bool
    credential_use: bool

    reasoning: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskClassification":
        return cls(
            operation_type=str(
                data.get("operation_type", "unknown")
            ),
            data_sensitivity=str(
                data.get("data_sensitivity", "unknown")
            ),
            external_side_effect=bool(
                data.get("external_side_effect", False)
            ),
            destructive=bool(
                data.get("destructive", False)
            ),
            credential_use=bool(
                data.get("credential_use", False)
            ),
            reasoning=str(
                data.get("reasoning", "")
            ),
        )


@dataclass(frozen=True)
class ApprovalDecision:
    """
    Result of the complete approval evaluation.

    Classification and authorization are deliberately kept separate.
    """

    status: ApprovalStatus
    classification: TaskClassification
    reasons: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.status == ApprovalStatus.ALLOW

    @property
    def requires_human_review(self) -> bool:
        return self.status == ApprovalStatus.REVIEW

    @property
    def denied(self) -> bool:
        return self.status == ApprovalStatus.DENY