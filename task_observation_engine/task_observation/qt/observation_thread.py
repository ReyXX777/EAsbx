from __future__ import annotations

from typing import Any, Mapping

from PySide6.QtCore import QObject, Signal, Slot

from ..models import ObservationSnapshot
from ..session import TaskObservationEngine, TaskObservationSession


class ObservationWorker(QObject):
    """Owns live observation state on the dedicated observation thread.

    The worker is the only Qt-side object allowed to mutate the active
    TaskObservationSession.

    The presentation layer communicates with this object through queued
    signals exposed by ObservationBridge.

    Responsibilities:

    - create live observation sessions
    - mutate collectors belonging to the active session
    - publish current snapshots
    - finish sessions
    - release the active session

    Persistence and feature derivation remain owned by the observation
    engine/session layer.
    """

    task_started = Signal(str)
    observation_updated = Signal(object)
    task_finished = Signal(object)
    worker_error = Signal(str)

    EVENT_SOURCE = "qt_observation_worker"

    def __init__(
        self,
        storage_root: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._engine = TaskObservationEngine(
            storage_root=storage_root,
        )

        self._session: TaskObservationSession | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    @Slot(str, str, object)
    def start_task(
        self,
        family_key: str,
        task_key: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Start a new observation session."""

        try:
            if self._session is not None:
                self.worker_error.emit(
                    "Cannot start a new task while another task is active."
                )
                return

            family_key = (family_key or "").strip()

            if not family_key:
                self.worker_error.emit(
                    "Cannot start an observation without a task family."
                )
                return

            task_key = (task_key or "").strip()

            self._session = self._engine.start(
                family_key,
                task_key=task_key,
                metadata=metadata,
            )

            self.task_started.emit(family_key)

            self.observation_updated.emit(
                self._session.snapshot(),
            )

        except Exception as exc:
            self.worker_error.emit(f"Task start error: {type(exc).__name__}: {exc}")

    @Slot()
    def finish_task(self) -> None:
        """Finish the active observation session.

        TaskObservationSession.finish() is deliberately responsible for
        producing the final snapshot, including any configured feature
        derivation/persistence performed by the observation engine.
        """

        session = self._session

        if session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            snapshot = session.finish()

            self._session = None

            self.task_finished.emit(
                snapshot,
            )

            self.observation_updated.emit(
                snapshot,
            )

        except Exception as exc:
            self.worker_error.emit(
                f"Task finalization error: {type(exc).__name__}: {exc}"
            )

    # ------------------------------------------------------------------
    # Discrete observations
    # ------------------------------------------------------------------

    @Slot(str, object)
    def record_discrete(
        self,
        name: str,
        value: Any = None,
    ) -> None:
        """Record a discrete observation on the active session."""

        session = self._session

        if session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            session.discrete.record(
                name,
                value,
            )

        except Exception as exc:
            self.worker_error.emit(
                "Discrete observation error: " f"{type(exc).__name__}: {exc}"
            )

    # ------------------------------------------------------------------
    # Continuous observations
    # ------------------------------------------------------------------

    @Slot(str, object)
    def record_continuous(
        self,
        name: str,
        value: Any = None,
    ) -> None:
        """Record a continuous observation on the active session."""

        session = self._session

        if session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            session.continuous.record(
                name,
                value,
            )

        except Exception as exc:
            self.worker_error.emit(
                "Continuous observation error: " f"{type(exc).__name__}: {exc}"
            )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @Slot(str, object)
    def record_event(
        self,
        event_type: str,
        payload: Any = None,
    ) -> None:
        """Record an event and its canonical trace representation."""

        session = self._session

        if session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            normalized_payload = (
                {}
                if payload is None
                else (
                    dict(payload)
                    if isinstance(payload, Mapping)
                    else {"value": payload}
                )
            )

            session.events.event(
                event_type,
                source=self.EVENT_SOURCE,
                payload=normalized_payload,
            )

            # Tool lifecycle events participate in both the event stream
            # and the canonical trace stream.
            if event_type in {
                "tool_started",
                "tool_completed",
                "tool_failed",
            }:
                tool_name = normalized_payload.get("tool_name")

                if tool_name:
                    path = normalized_payload.get("path")

                    trace_discrete = {
                        key: value
                        for key, value in normalized_payload.items()
                        if key not in {"tool_name", "path"}
                    }

                    trace_discrete["tool_name"] = str(tool_name)

                    session.events.trace(
                        event_type,
                        action=str(tool_name),
                        path=(str(path) if path is not None else None),
                        discrete=trace_discrete,
                    )

        except Exception as exc:
            self.worker_error.emit(
                "Event observation error: " f"{type(exc).__name__}: {exc}"
            )

    # ------------------------------------------------------------------
    # Snapshot publication
    # ------------------------------------------------------------------

    @Slot()
    def publish_current_state(self) -> None:
        """Publish the current raw observation snapshot."""

        session = self._session

        if session is None:
            return

        try:
            snapshot = session.snapshot()

            self.observation_updated.emit(
                snapshot,
            )

        except Exception as exc:
            self.worker_error.emit(f"Snapshot error: {type(exc).__name__}: {exc}")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    @Slot()
    def shutdown(self) -> None:
        """Release the active session reference.

        A live unfinished session is deliberately not finalized here.
        Normal persistence occurs through finish_task().
        """

        self._session = None
