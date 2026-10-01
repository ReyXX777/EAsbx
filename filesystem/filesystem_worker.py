from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

from agent_state_manager import AgentStateManager

from .filesystem_agent import FilesystemAgent
from .filesystem_gemini_planner import (
    GeminiFilesystemPlannerError,
    GeminiFilesystemToolPlanner,
)
from .filesystem_models import (
    FilesystemOperation,
    FilesystemResult,
)
from .filesystem_service import SandboxFilesystemService


class FilesystemExecutionWorker(QThread):
    """
    Qt worker responsible for executing an approved filesystem Task.

    The worker owns no filesystem security logic.

    Execution path:

        Worker
          ↓
        GeminiFilesystemToolPlanner
          ↓
        FilesystemAgent
          ↓
        SandboxFilesystemService
          ↓
        FilesystemOperations
          ↓
        SandboxValidator
          ↓
        test_filesystem
    """

    step_updated = Signal(str)

    task_finished = Signal(object)

    error_occurred = Signal(str)

    def __init__(
        self,
        task,
        api_key: str,
        filesystem_root: str | None = None,
    ):
        super().__init__()

        self.task = task

        self.api_key = api_key

        if filesystem_root is None:
            filesystem_root = str(
                Path(__file__).resolve().parent.parent / "test_filesystem"
            )

        self.filesystem_root = filesystem_root

        self.state_manager = AgentStateManager(task)

        self._cancel_requested = False

        self.agent: FilesystemAgent | None = None

    # ==============================================================
    # Public worker controls
    # ==============================================================

    def get_status(self) -> dict:
        return self.state_manager.get_status()

    def cancel(self) -> None:
        """
        Request cooperative cancellation.

        We do not terminate the QThread forcibly because doing so
        could interrupt an active filesystem operation.
        """

        self._cancel_requested = True

    # ==============================================================
    # QThread entry point
    # ==============================================================

    def run(self) -> None:

        try:

            self.state_manager.start_task()

            self.step_updated.emit(
                f"🚀 Starting filesystem task: " f"'{self.task.prompt}'"
            )

            # ------------------------------------------------------
            # Validate API key
            # ------------------------------------------------------

            if not self.api_key:
                raise ValueError("Gemini API key is missing.")

            # ------------------------------------------------------
            # Create sandbox service
            # ------------------------------------------------------

            self.step_updated.emit("🗂️ Initializing sandboxed filesystem...")

            service = SandboxFilesystemService(self.filesystem_root)

            # ------------------------------------------------------
            # Create Gemini planner
            # ------------------------------------------------------

            planner = GeminiFilesystemToolPlanner(api_key=self.api_key)

            # ------------------------------------------------------
            # Create filesystem agent
            # ------------------------------------------------------

            self.agent = FilesystemAgent(
                service=service,
                planner=planner,
            )

            # ------------------------------------------------------
            # Execute Gemini/tool loop
            # ------------------------------------------------------

            results, final_text = self.agent.run_interactive(
                self.task.prompt,
                on_result=self._on_tool_result,
                should_cancel=self._is_cancelled,
            )

            # ------------------------------------------------------
            # Cancellation check
            # ------------------------------------------------------

            if self._cancel_requested:

                self.state_manager.mark_cancelled()

                self.error_occurred.emit("Filesystem task cancelled by user.")

                return

            # ------------------------------------------------------
            # Complete canonical task
            # ------------------------------------------------------

            execution_result = {
                "final_text": final_text,
                "results": results,
                "filesystem_root": self.filesystem_root,
            }

            self.state_manager.mark_completed(execution_result)

            self.task_finished.emit(execution_result)

        except GeminiFilesystemPlannerError as exc:

            error_message = f"Filesystem planner error: {exc}"

            self.state_manager.mark_failed(error_message)

            self.error_occurred.emit(error_message)

        except Exception as exc:

            error_message = f"Filesystem agent failure: " f"{type(exc).__name__}: {exc}"

            self.state_manager.mark_failed(error_message)

            self.error_occurred.emit(error_message)

    # ==============================================================
    # Tool result callback
    # ==============================================================

    def _on_tool_result(
        self,
        operation: FilesystemOperation,
        result: FilesystemResult,
    ) -> None:

        # ----------------------------------------------------------
        # Record a canonical Task step.
        # ----------------------------------------------------------

        step = self.task.add_step(
            description=(f"{operation.operation.value}" f"({operation.path or '.'})"),
            action_type=operation.operation.value,
        )

        step_index = len(self.task.steps) - 1

        self.task.start_step(step_index)

        if result.success:

            step.complete(result.data)

            path_text = result.relative_path or operation.path or "."

            self.step_updated.emit(f"📂 {operation.operation.value}: " f"{path_text}")

        else:

            step.fail(result.message)

            self.step_updated.emit(
                f"❌ {operation.operation.value}: " f"{result.message}"
            )

    def _is_cancelled(self) -> bool:
        return self._cancel_requested
