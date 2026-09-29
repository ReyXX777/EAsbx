# task_models.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    """
    Lifecycle state of an entire task.

    A Task must always be in exactly one of these states.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """
    Lifecycle state of an individual task step.
    """

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    """
    A single logical step belonging to a Task.

    This object contains task-domain information only.
    It knows nothing about Qt, browser-use, Gemini, or the UI.
    """

    step_id: int
    description: str
    action_type: str

    status: StepStatus = StepStatus.PENDING
    risk_score: float = 0.0

    result: Optional[Any] = None
    error: Optional[str] = None

    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def start(self) -> None:
        """Mark this step as executing."""

        self.status = StepStatus.EXECUTING
        self.started_at = datetime.now(timezone.utc)
        self.error = None

    def complete(self, result: Any = None) -> None:
        """Mark this step as successfully completed."""

        self.status = StepStatus.COMPLETED
        self.result = result
        self.finished_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """Mark this step as failed."""

        self.status = StepStatus.FAILED
        self.error = error
        self.finished_at = datetime.now(timezone.utc)

    def cancel(self, reason: Optional[str] = None) -> None:
        """Mark this step as cancelled."""

        self.status = StepStatus.CANCELLED
        self.error = reason
        self.finished_at = datetime.now(timezone.utc)


@dataclass
class Task:
    """
    Canonical representation of an executable user task.

    This is the single source of truth for task state.

    It contains no UI or execution-engine dependencies.
    """

    prompt: str

    task_id: str = field(default_factory=lambda: str(uuid4()))

    status: TaskStatus = TaskStatus.PENDING

    steps: list[TaskStep] = field(default_factory=list)

    current_step_index: Optional[int] = None

    result: Optional[Any] = None
    error: Optional[str] = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def start(self) -> None:
        """Start task execution."""

        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.error = None

    def add_step(
        self,
        description: str,
        action_type: str,
        risk_score: float = 0.0,
    ) -> TaskStep:
        """Create and attach a new step to this task."""

        step = TaskStep(
            step_id=len(self.steps) + 1,
            description=description,
            action_type=action_type,
            risk_score=risk_score,
        )

        self.steps.append(step)

        return step

    def get_current_step(self) -> Optional[TaskStep]:
        """Return the currently executing step."""

        if self.current_step_index is None:
            return None

        if not 0 <= self.current_step_index < len(self.steps):
            return None

        return self.steps[self.current_step_index]

    def start_step(self, step_index: int) -> TaskStep:
        """Set and start a task step."""

        if not 0 <= step_index < len(self.steps):
            raise IndexError(
                f"Invalid task step index: {step_index}"
            )

        self.current_step_index = step_index

        step = self.steps[step_index]
        step.start()

        return step

    def complete(self, result: Any = None) -> None:
        """Mark the task as successfully completed."""

        self.status = TaskStatus.COMPLETED
        self.result = result
        self.finished_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """Mark the task as failed."""

        self.status = TaskStatus.FAILED
        self.error = error
        self.finished_at = datetime.now(timezone.utc)

        current_step = self.get_current_step()

        if current_step and current_step.status == StepStatus.EXECUTING:
            current_step.fail(error)

    def cancel(self, reason: str = "Task cancelled by user.") -> None:
        """Mark the task as cancelled."""

        self.status = TaskStatus.CANCELLED
        self.error = reason
        self.finished_at = datetime.now(timezone.utc)

        current_step = self.get_current_step()

        if current_step and current_step.status == StepStatus.EXECUTING:
            current_step.cancel(reason)

    def is_finished(self) -> bool:
        """Return True when the task reached a terminal state."""

        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }