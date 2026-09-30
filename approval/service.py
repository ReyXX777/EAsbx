from __future__ import annotations

from approval.jev_client import JevClient
from approval.models import (
    ApprovalResult,
    TaskRequest,
)
from approval.policy import ApprovalPolicy


class ApprovalService:
    """
    Single application-facing entry point for authorization.
    """

    def __init__(
        self,
        jev_client: JevClient | None = None,
        policy: ApprovalPolicy | None = None,
    ) -> None:

        self.jev_client = (
            jev_client
            or JevClient()
        )

        self.policy = (
            policy
            or ApprovalPolicy()
        )

    def evaluate(
        self,
        task: TaskRequest,
    ) -> ApprovalResult:

        jev_result = self.jev_client.evaluate(
            task
        )

        return self.policy.evaluate(
            task,
            jev_result
        )