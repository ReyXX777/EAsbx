from __future__ import annotations

from abc import ABC, abstractmethod

from .models import TaskClassification


class DecisionClassifier(ABC):
    """
    Interface for task-risk classification.

    The approval engine depends on this abstraction rather than
    depending directly on Gemini.
    """

    @abstractmethod
    def classify(
        self,
        task_prompt: str,
    ) -> TaskClassification:
        raise NotImplementedError