from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from agent_state_manager import AgentStateManager

from .compute.compute_service import ComputeService
from .filesystem_agent import FilesystemAgent
from .filesystem_gemini_planner import (
    GeminiFilesystemPlannerError,
    GeminiFilesystemToolPlanner,
)
from .filesystem_service import SandboxFilesystemService
from .tools.tool_factory import create_tool_dispatcher
from .tools.tool_models import ToolCall, ToolResult
from .filesystem_agent_events import FilesystemToolActivity
from task_observation_engine.task_observation import (
    TaskObservationEngine,
    TaskObservationSession,
)


class FilesystemExecutionWorker(QThread):
    """
    Qt worker responsible for executing an approved filesystem Task.

    The worker owns orchestration only.

    It does not implement filesystem operations, computation,
    tool registration, or tool dispatching.

    Execution path:

        Worker
          ↓
        SandboxFilesystemService
        ComputeService
          ↓
        Tool Factory
          ↓
        ToolDispatcher
          ├── FilesystemToolAdapter
          │       ↓
          │   SandboxFilesystemService
          │
          └── ComputeToolAdapter
                  ↓
              ComputeService
          ↓
        GeminiFilesystemToolPlanner
          ↓
        FilesystemAgent
    """

    step_updated = Signal(str)

    tool_started = Signal(object)

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

        observation_storage_root = (
            Path(__file__).resolve().parent.parent / "task_observation_data"
        )

        self.observation_engine = TaskObservationEngine(
            storage_root=str(observation_storage_root)
        )

        self.observation_session: TaskObservationSession | None = None

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
        could interrupt an active filesystem or compute operation.
        """

        self._cancel_requested = True

    # ==============================================================
    # QThread entry point
    # ==============================================================

    def run(self) -> None:

        try:

            self.state_manager.start_task()

            self.step_updated.emit(f"🚀 Starting filesystem task: '{self.task.prompt}'")

            self.observation_session = self.observation_engine.start(
                "filesystem",
                task_key=getattr(self.task, "id", "") or "",
                metadata={
                    "prompt": self.task.prompt,
                    "filesystem_root": self.filesystem_root,
                    "agent_type": "filesystem",
                },
            )

            self.observation_session.events.event(
                "task_started",
                source="filesystem_worker",
            )
            # ------------------------------------------------------
            # Validate API key
            # ------------------------------------------------------

            if not self.api_key:
                raise ValueError("Gemini API key is missing.")

            # ------------------------------------------------------
            # Create sandbox filesystem service
            # ------------------------------------------------------

            self.step_updated.emit("🗂️ Initializing sandboxed filesystem...")

            filesystem_service = SandboxFilesystemService(self.filesystem_root)

            # ------------------------------------------------------
            # Create deterministic compute service
            # ------------------------------------------------------

            self.step_updated.emit("🧮 Initializing compute service...")

            compute_service = ComputeService()

            # ------------------------------------------------------
            # Create generic tool dispatcher
            #
            # The factory owns all tool registration and adapter
            # composition. The worker does not know individual
            # filesystem or compute tools.
            # ------------------------------------------------------

            self.step_updated.emit("🔧 Initializing tool dispatcher...")

            tool_dispatcher = create_tool_dispatcher(
                filesystem_service=filesystem_service,
                compute_service=compute_service,
            )

            # ------------------------------------------------------
            # Create Gemini planner
            #
            # Gemini receives tool declarations from the generic
            # dispatcher. It does not receive filesystem services
            # or compute services directly.
            # ------------------------------------------------------

            self.step_updated.emit("🤖 Initializing Gemini filesystem planner...")

            planner = GeminiFilesystemToolPlanner(
                api_key=self.api_key,
                tool_dispatcher=tool_dispatcher,
            )

            # ------------------------------------------------------
            # Create filesystem agent
            # ------------------------------------------------------

            self.agent = FilesystemAgent(
                service=filesystem_service,
                planner=planner,
                tool_dispatcher=tool_dispatcher,
            )

            # ------------------------------------------------------
            # Execute Gemini/tool loop
            # ------------------------------------------------------

            results, final_text = self.agent.run_interactive(
                self.task.prompt,
                on_tool_call=self._on_tool_call,
                on_result=self._on_tool_result,
                should_cancel=self._is_cancelled,
            )

            # ------------------------------------------------------
            # Cancellation check
            # ------------------------------------------------------

            if self._cancel_requested:

                self.state_manager.mark_cancelled()

                if self.observation_session is not None:
                    self.observation_session.events.event(
                        "task_cancelled",
                        source="filesystem_worker",
                        payload={
                            "status": "cancelled",
                        },
                    )

                    self.observation_session.finish(
                        status="cancelled",
                    )

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
            if self.observation_session is not None:
                self.observation_session.events.event(
                    "task_completed",
                    source="filesystem_worker",
                    payload={
                        "status": "completed",
                    },
                )

                self.observation_session.finish(
                    status="completed",
                )
            self.task_finished.emit(execution_result)

        except GeminiFilesystemPlannerError as exc:

            error_message = f"Filesystem planner error: {exc}"

            self.state_manager.mark_failed(error_message)
            if self.observation_session is not None:
                self.observation_session.events.event(
                    "task_failed",
                    source="filesystem_worker",
                    payload={
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )

                self.observation_session.finish(
                    status="failed",
                )

            self.error_occurred.emit(error_message)

        except Exception as exc:

            error_message = f"Filesystem agent failure: " f"{type(exc).__name__}: {exc}"

            self.state_manager.mark_failed(error_message)
            if self.observation_session is not None:
                self.observation_session.events.event(
                    "task_failed",
                    source="filesystem_worker",
                    payload={
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )

                self.observation_session.finish(
                    status="failed",
                )
            self.error_occurred.emit(error_message)

    # ==============================================================
    # Generic tool start callback
    # ==============================================================

    def _on_tool_call(
        self,
        call: ToolCall,
    ) -> None:
        """
        Convert a generic ToolCall into an observable agent-activity
        event and emit it through Qt.

        The worker is the boundary between the framework-independent
        agent layer and the Qt application layer.
        """

        activity = FilesystemToolActivity(
            tool_name=call.name,
            arguments=dict(call.arguments or {}),
        )
        if self.observation_session is not None:
            arguments = dict(call.arguments or {})
            path = arguments.get("path")

            self.observation_session.events.event(
                "tool_started",
                source="filesystem_worker",
                payload={
                    "tool_name": call.name,
                    "path": path,
                },
            )

            self.observation_session.events.trace(
                "tool_started",
                action=call.name,
                path=path,
                discrete={
                    "tool_name": call.name,
                },
            )

        self.tool_started.emit(activity)

    # ==============================================================
    # Generic tool result callback
    # ==============================================================

    def _on_tool_result(
        self,
        call: ToolCall,
        result: ToolResult,
    ) -> None:
        """
        Record a canonical Task step from a generic tool execution.

        The worker intentionally does not inspect filesystem-specific
        operation models here.

        Both filesystem tools and compute tools arrive through the
        same ToolCall / ToolResult boundary.
        """

        arguments = call.arguments or {}

        path = arguments.get("path")

        if self.observation_session is not None:
            self.observation_session.events.event(
                "tool_completed" if result.success else "tool_failed",
                source="filesystem_worker",
                payload={
                    "tool_name": call.name,
                    "path": path,
                    "success": result.success,
                    "message": result.message,
                    "error": result.error,
                },
            )

            self.observation_session.discrete.record(
                "tool_success",
                result.success,
                source="filesystem_worker",
            )

            self.observation_session.discrete.record(
                "tool_name",
                call.name,
                source="filesystem_worker",
            )

            if path is not None:
                self.observation_session.discrete.record(
                    "path",
                    str(path),
                    source="filesystem_worker",
                )

            self.observation_session.events.trace(
                "tool_completed" if result.success else "tool_failed",
                action=call.name,
                path=path,
                discrete={
                    "success": result.success,
                },
            )

        if path:
            description = f"{call.name}({path})"
        else:
            description = call.name

        step = self.task.add_step(
            description=description,
            action_type=call.name,
        )

        step_index = len(self.task.steps) - 1

        self.task.start_step(step_index)

        if result.success:

            step.complete(result.data)

            location_text = path or result.message or "completed"

            self.step_updated.emit(f"🔧 {call.name}: {location_text}")

        else:

            error_text = result.error or result.message or "Tool execution failed."

            step.fail(error_text)

            self.step_updated.emit(f"❌ {call.name}: {error_text}")

    # ==============================================================
    # Cancellation
    # ==============================================================

    def _is_cancelled(self) -> bool:
        return self._cancel_requested
