from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from qt_theme import ResponsiveMetrics

from ..history import ObservationHistory
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


class ObservationWidget(QWidget):
    """Root presentation widget for the Observation Monitor.

    This class composes the independent presentation components.

    It does not create or mutate observation sessions.

    The filesystem agent owns the actual observation session.
    This widget reads persisted observations through ReplayAPI.

    Layout responsibilities are limited to:

    - responsive geometry,
    - splitter allocation,
    - minimum-size protection,
    - composition of observation panels.

    Visual styling is provided by the global MOCKAPP Qt theme.
    """

    def __init__(
        self,
        storage_root: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
        )

        self.storage_root = storage_root

        self.history = ObservationHistory(
            self.storage_root,
        )

        self._snapshot: ObservationSnapshot | None = None

        self._layout_initialized = False

        self._build_ui()

        self.refresh()





    def _build_ui(self) -> None:
        metrics = ResponsiveMetrics()

        root = QVBoxLayout(
            self,
        )

        root.setContentsMargins(
            metrics.margin(),
            metrics.margin(),
            metrics.margin(),
            metrics.margin(),
        )

        root.setSpacing(
            metrics.spacing(),
        )





        self.header = ObservationHeader()

        self.header.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.header.refresh_requested.connect(
            self.refresh,
        )

        root.addWidget(
            self.header,
        )





        self.main_splitter = QSplitter(
            Qt.Orientation.Horizontal,
        )

        self.main_splitter.setChildrenCollapsible(
            False,
        )

        self.main_splitter.setHandleWidth(
            metrics.splitter_handle(),
        )

        self.main_splitter.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )





        self.sidebar = ObservationSidebar()

        self.sidebar.setMinimumWidth(
            metrics.px(
                190,
                170,
            ),
        )

        self.sidebar.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

        self.sidebar.session_selected.connect(
            self._load_session,
        )

        self.main_splitter.addWidget(
            self.sidebar,
        )





        content = QWidget()

        content.setProperty(
            "role",
            "panel",
        )

        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        content_layout = QVBoxLayout(
            content,
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            metrics.spacing(),
        )





        self.top_splitter = QSplitter(
            Qt.Orientation.Horizontal,
        )

        self.top_splitter.setChildrenCollapsible(
            False,
        )

        self.top_splitter.setHandleWidth(
            metrics.splitter_handle(),
        )

        self.top_splitter.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.activity = ObservationActivity()

        self.activity.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.metrics = ObservationMetrics()

        self.metrics.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.top_splitter.addWidget(
            self.activity,
        )

        self.top_splitter.addWidget(
            self.metrics,
        )

        self.top_splitter.setStretchFactor(
            0,
            1,
        )

        self.top_splitter.setStretchFactor(
            1,
            1,
        )





        self.bottom_splitter = QSplitter(
            Qt.Orientation.Horizontal,
        )

        self.bottom_splitter.setChildrenCollapsible(
            False,
        )

        self.bottom_splitter.setHandleWidth(
            metrics.splitter_handle(),
        )

        self.bottom_splitter.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.continuous = ObservationContinuous()

        self.continuous.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.continuous.setMinimumWidth(
            metrics.panel_min_width(),
        )

        self.continuous.set_history(
            self.history,
        )

        self.trace = ObservationTrace()

        self.trace.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.trace.setMinimumWidth(
            metrics.panel_min_width(),
        )

        self.bottom_splitter.addWidget(
            self.continuous,
        )

        self.bottom_splitter.addWidget(
            self.trace,
        )

        self.bottom_splitter.setStretchFactor(
            0,
            1,
        )

        self.bottom_splitter.setStretchFactor(
            1,
            1,
        )





        content_layout.addWidget(
            self.top_splitter,
            1,
        )

        content_layout.addWidget(
            self.bottom_splitter,
            1,
        )





        self.main_splitter.addWidget(
            content,
        )

        self.main_splitter.setStretchFactor(
            0,
            0,
        )

        self.main_splitter.setStretchFactor(
            1,
            1,
        )

        root.addWidget(
            self.main_splitter,
            1,
        )





        self.activity.timeline.itemClicked.connect(
            self._activity_item_selected,
        )





    def _initialize_splitter_sizes(self) -> None:
        """Initialize splitter geometry from the current available size.

        This method only establishes sensible starting geometry.

        After initialization, the user remains free to move the
        splitters manually.
        """

        if self._layout_initialized:
            return

        if self.width() <= 0 or self.height() <= 0:
            return

        metrics = ResponsiveMetrics.for_widget(
            self,
        )

        sidebar_width = metrics.sidebar_width()

        total_width = self.main_splitter.width()

        if total_width <= sidebar_width:
            sidebar_width = max(
                metrics.px(
                    180,
                    160,
                ),
                total_width // 5,
            )

        content_width = max(
            1,
            total_width - sidebar_width,
        )

        self.main_splitter.setSizes(
            [
                sidebar_width,
                content_width,
            ],
        )

        content_width = self.main_splitter.sizes()[1]

        if content_width > 0:
            left_width = max(
                metrics.panel_min_width(),
                content_width // 2,
            )

            right_width = max(
                metrics.panel_min_width(),
                content_width - left_width,
            )

            self.top_splitter.setSizes(
                [
                    left_width,
                    right_width,
                ],
            )

            self.bottom_splitter.setSizes(
                [
                    left_width,
                    right_width,
                ],
            )

        self._layout_initialized = True

    def resizeEvent(
        self,
        event,
    ) -> None:
        super().resizeEvent(
            event,
        )

        self._initialize_splitter_sizes()





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





    def _activity_item_selected(
        self,
        item,
    ) -> None:
        trace = item.data(
            Qt.ItemDataRole.UserRole,
        )

        if isinstance(
            trace,
            TracePoint,
        ):
            self.trace.set_trace(
                trace,
            )





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





    def showEvent(
        self,
        event,
    ) -> None:
        super().showEvent(
            event,
        )

        self._initialize_splitter_sizes()

    def closeEvent(
        self,
        event,
    ) -> None:
        super().closeEvent(
            event,
        )
