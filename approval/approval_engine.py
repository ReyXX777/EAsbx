from __future__ import annotations

from .classifier import DecisionClassifier
from .models import ApprovalDecision
from .policy_engine import ApprovalPolicyEngine


class ApprovalEngine:
    """
    Coordinates classification and deterministic authorization.

    Classification answers:
        "What is this task asking the agent to do?"

    Policy answers:
        "Given those characteristics, what authorization state
         should the application enter?"
    """

    def __init__(
        self,
        classifier: DecisionClassifier,
        policy_engine: ApprovalPolicyEngine,
    ):
        self.classifier = classifier
        self.policy_engine = policy_engine

    def evaluate(
        self,
        task_prompt: str,
    ) -> ApprovalDecision:

        classification = self.classifier.classify(
            task_prompt
        )

        return self.policy_engine.evaluate(
            classification
        )