from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..models import (
    ObservationSnapshot,
    TracePoint,
)
from ..replay import ReplayAPI

from .observation_activity import ObservationActivity
from .observation_continuous import ObservationContinuous
from .observation_header import ObservationHeader
from .observation_metrics import ObservationMetrics
from .observation_sidebar import ObservationSidebar
from .observation_trace import ObservationTrace
from ..history import ObservationHistory


class ObservationWidget(QWidget):
    """Root presentation widget for the Observation Monitor.

    This class composes the independent presentation components.

    It does not create or mutate observation sessions.

    The filesystem agent owns the actual observation session.
    This widget reads persisted observations through ReplayAPI.
    """

    def __init__(
        self,
        storage_root: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.storage_root = storage_root

        self.history = ObservationHistory(
            self.storage_root,
        )

        self._snapshot: ObservationSnapshot | None = None

        self._build_ui()

        self.refresh()

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.setSpacing(0)

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        self.header = ObservationHeader()

        self.header.refresh_requested.connect(
            self.refresh,
        )

        root.addWidget(
            self.header,
        )

        # --------------------------------------------------------------
        # Main horizontal layout
        # --------------------------------------------------------------

        main_splitter = QSplitter(
            Qt.Horizontal,
        )

        # --------------------------------------------------------------
        # Sidebar
        # --------------------------------------------------------------

        self.sidebar = ObservationSidebar()

        self.sidebar.session_selected.connect(
            self._load_session,
        )

        main_splitter.addWidget(
            self.sidebar,
        )

        # --------------------------------------------------------------
        # Four-panel display area
        # --------------------------------------------------------------

        content = QWidget()

        content_layout = QVBoxLayout(
            content,
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(0)

        # ==============================================================
        # Row 1
        # ==============================================================

        top_splitter = QSplitter(
            Qt.Horizontal,
        )

        self.activity = ObservationActivity()

        self.metrics = ObservationMetrics()

        top_splitter.addWidget(
            self.activity,
        )

        top_splitter.addWidget(
            self.metrics,
        )

        # ==============================================================
        # Row 2
        # ==============================================================

        bottom_splitter = QSplitter(
            Qt.Horizontal,
        )

        self.continuous = ObservationContinuous()

        self.continuous.set_history(
            self.history,
        )

        self.trace = ObservationTrace()

        bottom_splitter.addWidget(
            self.continuous,
        )

        bottom_splitter.addWidget(
            self.trace,
        )

        content_layout.addWidget(
            top_splitter,
            1,
        )

        content_layout.addWidget(
            bottom_splitter,
            1,
        )

        main_splitter.addWidget(
            content,
        )

        main_splitter.setSizes(
            [
                240,
                960,
            ]
        )

        root.addWidget(
            main_splitter,
            1,
        )

        # --------------------------------------------------------------
        # Activity -> Trace
        # --------------------------------------------------------------

        self.activity.timeline.itemClicked.connect(
            self._activity_item_selected,
        )

    # ==================================================================
    # Refresh
    # ==================================================================

    def refresh(self) -> None:
        try:
            self.history.refresh()
            replay = ReplayAPI(
                self.storage_root,
            )

            session_ids = replay.session_ids()

        except Exception as exc:
            self._set_error(
                f"History error: {exc}",
            )
            return
        self.continuous.refresh()

        sessions: list[dict] = []

        for session_id in session_ids:
            try:
                snapshot = replay.session(
                    str(session_id),
                )

            except Exception:
                continue

            sessions.append(
                self._session_summary(
                    snapshot,
                )
            )

        self.sidebar.set_sessions(
            sessions,
        )

        self.header.set_live(
            False,
        )

        if not sessions:
            self._clear_display()

    # ==================================================================
    # Session loading
    # ==================================================================

    def _load_session(
        self,
        session_id: str,
    ) -> None:
        try:
            replay = ReplayAPI(
                self.storage_root,
            )

            snapshot = replay.session(
                session_id,
            )

        except Exception as exc:
            self._set_error(
                f"Replay error: {exc}",
            )
            return

        self._display_snapshot(
            snapshot,
        )

    # ==================================================================
    # Snapshot
    # ==================================================================

    def _display_snapshot(
        self,
        snapshot: ObservationSnapshot,
    ) -> None:
        if not isinstance(
            snapshot,
            ObservationSnapshot,
        ):
            self._set_error(
                "Received an invalid observation snapshot.",
            )
            return

        self._snapshot = snapshot

        self.activity.set_snapshot(
            snapshot,
        )

        self.metrics.set_snapshot(
            snapshot,
        )

        self.continuous.refresh()

        self.trace.clear()

        self._update_header(
            snapshot,
        )

    def _update_header(
        self,
        snapshot: ObservationSnapshot,
    ) -> None:
        status = str(
            snapshot.status,
        ).lower()

        self.header.live_label.setText(
            f"● {status.upper()}",
        )

    # ==================================================================
    # Activity selection
    # ==================================================================

    def _activity_item_selected(
        self,
        item,
    ) -> None:
        trace = item.data(
            256,
        )

        if isinstance(
            trace,
            TracePoint,
        ):
            self.trace.set_trace(
                trace,
            )

    # ==================================================================
    # Session summary
    # ==================================================================

    @staticmethod
    def _session_summary(
        snapshot: ObservationSnapshot,
    ) -> dict:
        identity = snapshot.identity

        return {
            "session_id": str(
                identity.session_id,
            ),
            "family": str(
                identity.family_key,
            ),
            "status": str(
                snapshot.status,
            ),
            "started_at": snapshot.started_at,
            "finished_at": snapshot.finished_at,
        }

    # ==================================================================
    # Empty/error state
    # ==================================================================

    def _clear_display(self) -> None:
        self._snapshot = None

        self.activity.clear()
        self.metrics.clear()
        self.continuous.clear()
        self.trace.clear()

        self.header.set_live(
            False,
        )

    def _set_error(
        self,
        message: str,
    ) -> None:
        self._clear_display()

        self.header.live_label.setText(
            f"● ERROR: {message}",
        )

    # ==================================================================
    # Lifecycle
    # ==================================================================

    def closeEvent(self, event) -> None:
        super().closeEvent(event)
