from __future__ import annotations

from typing import Any, Mapping

from PySide6.QtCore import QObject, QThread, Signal, Slot

from .observation_thread import ObservationWorker


class ObservationBridge(QObject):
    """Thread-safe Qt bridge for the observation worker.

    UI code communicates only with this object.

    The bridge owns the worker thread and forwards requests to the
    ObservationWorker using Qt's queued signal/slot mechanism.
    """

    task_started = Signal(str)
    observation_updated = Signal(object)
    task_finished = Signal(object)
    error = Signal(str)

    request_start = Signal(str, str, object)
    request_discrete = Signal(str, object)
    request_continuous = Signal(str, object)
    request_event = Signal(str, object)
    request_snapshot = Signal()
    request_finish = Signal()
    request_shutdown = Signal()

    def __init__(
        self,
        storage_root: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._closed = False

        self._thread = QThread(self)

        self._worker = ObservationWorker(
            storage_root,
        )

        self._worker.moveToThread(
            self._thread,
        )

        # --------------------------------------------------------------
        # Requests: UI -> worker
        # --------------------------------------------------------------

        self.request_start.connect(
            self._worker.start_task,
        )

        self.request_discrete.connect(
            self._worker.record_discrete,
        )

        self.request_continuous.connect(
            self._worker.record_continuous,
        )

        self.request_event.connect(
            self._worker.record_event,
        )

        self.request_snapshot.connect(
            self._worker.publish_current_state,
        )

        self.request_finish.connect(
            self._worker.finish_task,
        )

        self.request_shutdown.connect(
            self._worker.shutdown,
        )

        # --------------------------------------------------------------
        # Results: worker -> UI
        # --------------------------------------------------------------

        self._worker.task_started.connect(
            self.task_started,
        )

        self._worker.observation_updated.connect(
            self.observation_updated,
        )

        self._worker.task_finished.connect(
            self.task_finished,
        )

        self._worker.worker_error.connect(
            self.error,
        )

        self._thread.start()

    # ------------------------------------------------------------------
    # Public commands
    # ------------------------------------------------------------------

    @Slot(str, str, object)
    def start_task(
        self,
        family_key: str,
        task_key: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Request creation of a new observation session."""

        if self._closed:
            return

        self.request_start.emit(
            family_key,
            task_key,
            metadata,
        )

    @Slot(str, object)
    def record_discrete(
        self,
        name: str,
        value: Any = None,
    ) -> None:
        """Request a discrete observation."""

        if self._closed:
            return

        self.request_discrete.emit(
            name,
            value,
        )

    @Slot(str, object)
    def record_continuous(
        self,
        name: str,
        value: Any = None,
    ) -> None:
        """Request a continuous observation."""

        if self._closed:
            return

        self.request_continuous.emit(
            name,
            value,
        )

    @Slot(str, object)
    def record_event(
        self,
        event_type: str,
        payload: Any = None,
    ) -> None:
        """Request an event observation."""

        if self._closed:
            return

        self.request_event.emit(
            event_type,
            payload,
        )

    def request_current_snapshot(self) -> None:
        """Request publication of the current live snapshot."""

        if self._closed:
            return

        self.request_snapshot.emit()

    def finish_task(self) -> None:
        """Request finalization of the active observation session."""

        if self._closed:
            return

        self.request_finish.emit()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Stop the worker thread safely and release Qt resources."""

        if self._closed:
            return

        self._closed = True

        if not self._thread.isRunning():
            return

        self.request_shutdown.emit()
        self._thread.quit()

        if not self._thread.wait(3000):
            self._thread.terminate()
            self._thread.wait(1000)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
