from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from ..session import TaskObservationEngine


class ObservationWorker(QObject):
    """Owns mutable observation state on a dedicated worker thread.

    No Qt widget should directly manipulate a TaskObservationSession.

    The worker receives requests through queued Qt signals and emits
    immutable-ish snapshot objects back to the presentation layer.
    """

    task_started = Signal(str)
    observation_updated = Signal(object)
    task_finished = Signal(object)
    worker_error = Signal(str)

    def __init__(self, storage_root: str, parent: QObject | None = None):
        super().__init__(parent)

        self._engine = TaskObservationEngine(storage_root)
        self._session = None

    @Slot(str)
    def start_task(self, family_key: str) -> None:
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

            self._session = self._engine.start(family_key)

            self.task_started.emit(family_key)

        except Exception as exc:
            self.worker_error.emit(f"{type(exc).__name__}: {exc}")

    @Slot(str, object)
    def record_discrete(self, name: str, value: Any) -> None:
        """Record one discrete feature.

        Missing values are deliberately allowed.
        """

        if self._session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            self._session.discrete.record(
                name,
                value,
            )

        except Exception as exc:
            self.worker_error.emit(
                f"Discrete observation error: {type(exc).__name__}: {exc}"
            )

    @Slot(str, object)
    def record_continuous(self, name: str, value: Any) -> None:
        """Record one continuous feature.

        Invalid/missing values are allowed to reach the collector, which
        already defines the prototype's non-halting behaviour.
        """

        if self._session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            self._session.continuous.record(
                name,
                value,
            )

        except Exception as exc:
            self.worker_error.emit(
                f"Continuous observation error: " f"{type(exc).__name__}: {exc}"
            )

    @Slot(str, object)
    def record_event(self, event_type: str, payload: Any = None) -> None:
        """Record a generic observation event when the session supports it.

        Stage 6B intentionally does not assume a particular event collector
        implementation. This keeps the Qt layer compatible with the current
        collector implementation while allowing richer event models later.
        """

        if self._session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            collector = getattr(self._session, "events", None)

            if collector is None:
                collector = getattr(self._session, "trace", None)

            if collector is None:
                # Event collection is optional at this stage.
                return

            record_method = getattr(collector, "record", None)

            if record_method is None:
                return

            record_method(
                event_type,
                payload,
            )

        except Exception as exc:
            self.worker_error.emit(
                f"Event observation error: " f"{type(exc).__name__}: {exc}"
            )

    @Slot()
    def publish_current_state(self) -> None:
        """Publish the current state when the session implementation supports it.

        The existing session API guarantees finish(), but not necessarily
        an intermediate snapshot API. Therefore this method is deliberately
        conservative.
        """

        if self._session is None:
            return

        try:
            snapshot_method = getattr(
                self._session,
                "snapshot",
                None,
            )

            if snapshot_method is None:
                return

            snapshot = snapshot_method()

            self.observation_updated.emit(snapshot)

        except Exception as exc:
            self.worker_error.emit(f"Snapshot error: {type(exc).__name__}: {exc}")

    @Slot()
    def finish_task(self) -> None:
        """Finish the active observation session."""

        if self._session is None:
            self.worker_error.emit("No active observation session.")
            return

        try:
            snapshot = self._session.finish()

            self._session = None

            self.task_finished.emit(snapshot)
            self.observation_updated.emit(snapshot)

        except Exception as exc:
            self.worker_error.emit(
                f"Task finalization error: " f"{type(exc).__name__}: {exc}"
            )

    @Slot()
    def shutdown(self) -> None:
        """Release the active session reference."""

        self._session = None
