

from __future__ import annotations

from typing import Any, Optional

from task_models import Task, TaskStatus


class AgentStateManager:
    """
    Adapter responsible for observing and updating a Task's execution state.

    The Task object is the canonical source of truth.

    This class intentionally contains no Qt code and no browser-use
    dependencies so it remains independently testable.
    """

    def __init__(self, task: Task):
        self.task = task

    def start_task(self) -> None:
        """Transition the task into the running state."""

        self.task.start()

    def record_step(self, agent_instance: Optional[Any] = None) -> str:
        """
        Record information about an agent execution step.

        browser-use history is treated as an optional source of
        descriptive information only. It does not own our task state.
        """

        current_step = self.task.get_current_step()

        if current_step is None:
            return "Agent executed a step."

        last_action_desc = "Processing step..."

        if agent_instance is not None:
            history = getattr(agent_instance, "history", None)

            if history is not None:
                model_actions = getattr(history, "model_actions", None)

                if callable(model_actions):
                    actions = model_actions()

                    if actions:
                        last_action_desc = str(actions[-1])

        return (
            f"Step {current_step.step_id}: "
            f"{last_action_desc[:120]}"
        )

    def mark_completed(self, result: Any = None) -> None:
        """Mark the task as successfully completed."""

        self.task.complete(result)

    def mark_failed(self, error_message: str) -> None:
        """Mark the task as failed."""

        self.task.fail(error_message)

    def mark_cancelled(
        self,
        reason: str = "Task cancelled by user.",
    ) -> None:
        """Mark the task as cancelled."""

        self.task.cancel(reason)

    def get_status(self) -> dict:
        """
        Return a UI/API-friendly snapshot.

        The Task itself remains the source of truth.
        """

        current_step = self.task.get_current_step()

        return {
            "task_id": self.task.task_id,
            "status": self.task.status.value,
            "current_step": (
                current_step.step_id
                if current_step is not None
                else 0
            ),
            "last_action": (
                current_step.description
                if current_step is not None
                else "Not started"
            ),
            "error": self.task.error,
        }