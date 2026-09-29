# task_graph.py

from __future__ import annotations

from typing import Optional

from task_models import Task, TaskStatus, TaskStep

class TaskGraph:
    """
    Execution-oriented view of a Task.

    TaskGraph manages the logical sequence of TaskStep objects,
    while Task remains the canonical owner of task state.

    This class contains no Qt, browser-use, Gemini, or UI logic.
    """

    def __init__(self, task: Task):
        self.task = task

    @property
    def steps(self) -> list[TaskStep]:
        """Return the task's steps."""

        return self.task.steps

    def add_step(
        self,
        description: str,
        action_type: str,
        risk_score: float = 0.0,
    ) -> TaskStep:
        """Add a new step to the task."""

        return self.task.add_step(
            description=description,
            action_type=action_type,
            risk_score=risk_score,
        )

    def get_current_step(self) -> Optional[TaskStep]:
        """Return the currently executing step."""

        return self.task.get_current_step()

    def start_step(self, step_index: int) -> TaskStep:
        """Start a specific step."""

        return self.task.start_step(step_index)

    def advance(self) -> Optional[TaskStep]:
        """
        Complete the current step and move to the next pending step.

        Returns the next step, or None if there are no more steps.
        """

        current_step = self.get_current_step()

        if current_step is not None:
            current_step.complete()

        next_index = (
            0
            if self.task.current_step_index is None
            else self.task.current_step_index + 1
        )

        if next_index >= len(self.steps):
            self.task.current_step_index = None
            return None

        self.task.current_step_index = next_index

        next_step = self.steps[next_index]
        next_step.start()

        return next_step

    def reset(self) -> None:
        """Reset the graph to its initial pending state."""
        
        self.task.current_step_index = None
        self.task.status = TaskStatus.PENDING

        for step in self.steps:
            step.status = step.status.PENDING
            step.result = None
            step.error = None
            step.started_at = None
            step.finished_at = None