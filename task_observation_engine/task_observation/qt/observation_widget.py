from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import (
    ObservationSnapshot,
    TaskEvent,
    TracePoint,
)
from ..replay import ReplayAPI
from .observation_bridge import ObservationBridge
from .observation_plot import ObservationPlot


class ObservationWidget(QWidget):
    """Qt visualization surface for task observations.

    The widget is a presentation component.

    It:

    - starts and finishes live observation sessions through
      ObservationBridge
    - displays live snapshots
    - displays persisted snapshots through ReplayAPI
    - visualizes discrete observations
    - visualizes continuous observations
    - displays recorded events and traces

    It does not own mutable observation-session state.
    """

    def __init__(
        self,
        storage_root: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.storage_root = storage_root

        self.bridge = ObservationBridge(
            storage_root,
            self,
        )

        self._snapshot: ObservationSnapshot | None = None

        self._build_ui()
        self._connect_bridge()

        self.refresh_history()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        root.setSpacing(6)

        # ----------------------------------------------------------------
        # Toolbar
        # ----------------------------------------------------------------

        toolbar = QHBoxLayout()

        toolbar.addWidget(
            QLabel("Family:"),
        )

        self.family_field = QComboBox()
        self.family_field.setEditable(True)
        self.family_field.setPlaceholderText(
            "Task family",
        )

        toolbar.addWidget(
            self.family_field,
            1,
        )

        self.start_button = QPushButton(
            "Start Observation",
        )

        self.finish_button = QPushButton(
            "Finish",
        )

        self.refresh_button = QPushButton(
            "Refresh History",
        )

        self.start_button.clicked.connect(
            self._start_task,
        )

        self.finish_button.clicked.connect(
            self._finish_task,
        )

        self.refresh_button.clicked.connect(
            self.refresh_history,
        )

        toolbar.addWidget(
            self.start_button,
        )

        toolbar.addWidget(
            self.finish_button,
        )

        toolbar.addWidget(
            self.refresh_button,
        )

        root.addLayout(
            toolbar,
        )

        # ----------------------------------------------------------------
        # Status
        # ----------------------------------------------------------------

        self.status_label = QLabel(
            "No active observation.",
        )

        root.addWidget(
            self.status_label,
        )

        # ----------------------------------------------------------------
        # Main horizontal splitter
        # ----------------------------------------------------------------

        splitter = QSplitter(
            Qt.Horizontal,
        )

        # ================================================================
        # History
        # ================================================================

        history_group = QGroupBox(
            "Stored Sessions",
        )

        history_layout = QVBoxLayout(
            history_group,
        )

        self.history_list = QListWidget()

        self.history_list.itemClicked.connect(
            self._load_history_item,
        )

        history_layout.addWidget(
            self.history_list,
        )

        splitter.addWidget(
            history_group,
        )

        # ================================================================
        # Right-side content
        # ================================================================

        right = QWidget()

        right_layout = QVBoxLayout(
            right,
        )

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        # ----------------------------------------------------------------
        # Session metadata
        # ----------------------------------------------------------------

        metadata_group = QGroupBox(
            "Session",
        )

        metadata_layout = QFormLayout(
            metadata_group,
        )

        self.session_id_label = QLabel("-")
        self.family_label = QLabel("-")
        self.session_status_label = QLabel("-")
        self.started_at_label = QLabel("-")
        self.finished_at_label = QLabel("-")

        metadata_layout.addRow(
            "Session ID:",
            self.session_id_label,
        )

        metadata_layout.addRow(
            "Family:",
            self.family_label,
        )

        metadata_layout.addRow(
            "Status:",
            self.session_status_label,
        )

        metadata_layout.addRow(
            "Started:",
            self.started_at_label,
        )

        metadata_layout.addRow(
            "Finished:",
            self.finished_at_label,
        )

        right_layout.addWidget(
            metadata_group,
        )

        # ----------------------------------------------------------------
        # Continuous feature selector
        # ----------------------------------------------------------------

        selector_layout = QHBoxLayout()

        selector_layout.addWidget(
            QLabel("Continuous feature:"),
        )

        self.feature_selector = QComboBox()

        self.feature_selector.currentTextChanged.connect(
            self._continuous_feature_changed,
        )

        selector_layout.addWidget(
            self.feature_selector,
            1,
        )

        right_layout.addLayout(
            selector_layout,
        )

        # ----------------------------------------------------------------
        # Continuous plot
        # ----------------------------------------------------------------

        self.plot = ObservationPlot()

        right_layout.addWidget(
            self.plot,
            2,
        )

        # ----------------------------------------------------------------
        # Lower vertical splitter
        # ----------------------------------------------------------------

        lower_splitter = QSplitter(
            Qt.Vertical,
        )

        # ================================================================
        # Discrete features
        # ================================================================

        discrete_group = QGroupBox(
            "Discrete Features",
        )

        discrete_layout = QVBoxLayout(
            discrete_group,
        )

        self.discrete_table = QTableWidget()

        self.discrete_table.setColumnCount(
            2,
        )

        self.discrete_table.setHorizontalHeaderLabels(
            [
                "Feature",
                "Value",
            ],
        )

        self.discrete_table.setEditTriggers(
            QTableWidget.NoEditTriggers,
        )

        discrete_layout.addWidget(
            self.discrete_table,
        )

        lower_splitter.addWidget(
            discrete_group,
        )

        # ================================================================
        # Events / traces
        # ================================================================

        event_group = QGroupBox(
            "Events / Trace",
        )

        event_layout = QVBoxLayout(
            event_group,
        )

        self.event_table = QTableWidget()

        self.event_table.setColumnCount(
            4,
        )

        self.event_table.setHorizontalHeaderLabels(
            [
                "Type",
                "Name / Action",
                "Source / Path",
                "Payload / Values",
            ],
        )

        self.event_table.setEditTriggers(
            QTableWidget.NoEditTriggers,
        )

        event_layout.addWidget(
            self.event_table,
        )

        lower_splitter.addWidget(
            event_group,
        )

        right_layout.addWidget(
            lower_splitter,
            2,
        )

        splitter.addWidget(
            right,
        )

        splitter.setSizes(
            [
                220,
                800,
            ],
        )

        root.addWidget(
            splitter,
            1,
        )

        self._set_running_state(
            False,
        )

    # ==================================================================
    # Bridge
    # ==================================================================

    def _connect_bridge(self) -> None:
        self.bridge.task_started.connect(
            self._on_task_started,
        )

        self.bridge.observation_updated.connect(
            self._display_snapshot,
        )

        self.bridge.task_finished.connect(
            self._on_task_finished,
        )

        self.bridge.error.connect(
            self._on_error,
        )

    # ==================================================================
    # Commands
    # ==================================================================

    def _start_task(self) -> None:
        family = self.family_field.currentText().strip()

        if not family:
            self.status_label.setText("Enter a task family.")
            return

        self.bridge.start_task(
            family,
        )

    def _finish_task(self) -> None:
        self.bridge.finish_task()

    # ==================================================================
    # Worker events
    # ==================================================================

    def _on_task_started(
        self,
        family: str,
    ) -> None:
        self.status_label.setText(f"Collecting: {family}")

        self.family_label.setText(
            family,
        )

        self.session_status_label.setText(
            "running",
        )

        self._set_running_state(
            True,
        )

    def _on_task_finished(
        self,
        snapshot: object,
    ) -> None:
        if not isinstance(
            snapshot,
            ObservationSnapshot,
        ):
            self._on_error("Worker returned an invalid observation snapshot.")
            return

        self.status_label.setText("Observation completed.")

        self._display_snapshot(
            snapshot,
        )

        self._set_running_state(
            False,
        )

        self.refresh_history()

    def _on_error(
        self,
        message: str,
    ) -> None:
        self.status_label.setText(f"Observation error: {message}")

    def _set_running_state(
        self,
        running: bool,
    ) -> None:
        self.start_button.setEnabled(
            not running,
        )

        self.finish_button.setEnabled(
            running,
        )

    # ==================================================================
    # Snapshot display
    # ==================================================================

    def _display_snapshot(
        self,
        snapshot: object,
    ) -> None:
        if not isinstance(
            snapshot,
            ObservationSnapshot,
        ):
            self._on_error("Received an invalid observation snapshot.")
            return

        self._snapshot = snapshot

        identity = snapshot.identity

        self.session_id_label.setText(
            str(identity.session_id),
        )

        self.family_label.setText(
            str(identity.family_key),
        )

        self.session_status_label.setText(
            str(snapshot.status),
        )

        self.started_at_label.setText(
            self._safe_text(snapshot.started_at),
        )

        self.finished_at_label.setText(
            self._safe_text(snapshot.finished_at),
        )

        self._display_discrete(
            snapshot.discrete,
        )

        self._display_continuous(
            snapshot.continuous,
        )

        self._display_events(
            snapshot,
        )

        self._set_running_state(
            snapshot.status == "running",
        )

    # ==================================================================
    # Discrete observations
    # ==================================================================

    def _display_discrete(
        self,
        observations,
    ) -> None:
        self.discrete_table.setRowCount(
            0,
        )

        for observation in observations:
            row = self.discrete_table.rowCount()

            self.discrete_table.insertRow(
                row,
            )

            self.discrete_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    self._safe_text(
                        observation.name,
                    )
                ),
            )

            self.discrete_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    self._safe_text(
                        observation.value,
                    )
                ),
            )

        self.discrete_table.resizeColumnsToContents()

    # ==================================================================
    # Continuous observations
    # ==================================================================

    def _display_continuous(
        self,
        observations,
    ) -> None:
        current = self.feature_selector.currentText()

        self.feature_selector.blockSignals(
            True,
        )

        try:
            self.feature_selector.clear()

            names: list[str] = []

            for observation in observations:
                name = str(
                    observation.name,
                )

                if name and name not in names:
                    names.append(name)

            self.feature_selector.addItems(
                names,
            )

            if current in names:
                self.feature_selector.setCurrentText(
                    current,
                )

        finally:
            self.feature_selector.blockSignals(
                False,
            )

        self._render_selected_continuous(
            observations,
        )

    def _continuous_feature_changed(
        self,
        _name: str,
    ) -> None:
        snapshot = self._snapshot

        if snapshot is None:
            return

        self._render_selected_continuous(
            snapshot.continuous,
        )

    def _render_selected_continuous(
        self,
        observations,
    ) -> None:
        selected = self.feature_selector.currentText()

        if not selected:
            self.plot.clear()
            return

        values: list[float] = []

        for observation in observations:
            if observation.name != selected:
                continue

            value = observation.value

            if value is None:
                continue

            try:
                values.append(
                    float(value),
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        self.plot.set_data(
            values,
            selected,
        )

    # ==================================================================
    # Events / traces
    # ==================================================================

    def _display_events(
        self,
        snapshot: ObservationSnapshot,
    ) -> None:
        self.event_table.setRowCount(
            0,
        )

        for event in snapshot.events:
            if not isinstance(event, TaskEvent):
                continue

            row = self.event_table.rowCount()

            self.event_table.insertRow(
                row,
            )

            self._set_event_row(
                row=row,
                event_type="event",
                name=event.name,
                source_or_path=event.source,
                payload_or_values=event.payload,
            )

        for trace in snapshot.traces:
            if not isinstance(trace, TracePoint):
                continue

            row = self.event_table.rowCount()

            self.event_table.insertRow(
                row,
            )

            values = {
                "discrete": dict(trace.discrete),
                "continuous": dict(trace.continuous),
            }

            self._set_event_row(
                row=row,
                event_type=trace.phase,
                name=trace.action,
                source_or_path=trace.path,
                payload_or_values=values,
            )

        self.event_table.resizeColumnsToContents()

    def _set_event_row(
        self,
        row: int,
        event_type: Any,
        name: Any,
        source_or_path: Any,
        payload_or_values: Any,
    ) -> None:
        values = self._safe_text(payload_or_values)

        self.event_table.setItem(
            row,
            0,
            QTableWidgetItem(
                self._safe_text(event_type),
            ),
        )

        self.event_table.setItem(
            row,
            1,
            QTableWidgetItem(
                self._safe_text(name),
            ),
        )

        self.event_table.setItem(
            row,
            2,
            QTableWidgetItem(
                self._safe_text(source_or_path),
            ),
        )

        self.event_table.setItem(
            row,
            3,
            QTableWidgetItem(
                values,
            ),
        )

    # ==================================================================
    # Replay / history
    # ==================================================================

    def refresh_history(self) -> None:
        try:
            replay = ReplayAPI(
                self.storage_root,
            )

            session_ids = replay.session_ids()

        except Exception as exc:
            self.status_label.setText(f"History error: {exc}")
            return

        self.history_list.clear()

        for session_id in session_ids:
            item = QListWidgetItem(
                str(session_id),
            )

            item.setData(
                Qt.UserRole,
                str(session_id),
            )

            self.history_list.addItem(
                item,
            )

    def _load_history_item(
        self,
        item: QListWidgetItem,
    ) -> None:
        session_id = item.data(
            Qt.UserRole,
        )

        if not session_id:
            return

        try:
            replay = ReplayAPI(
                self.storage_root,
            )

            snapshot = replay.session(
                str(session_id),
            )

            self._display_snapshot(
                snapshot,
            )

            self.status_label.setText(f"Loaded session: {session_id}")

            self._set_running_state(
                False,
            )

        except Exception as exc:
            self.status_label.setText(f"Replay error: {exc}")

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _safe_text(
        value: Any,
    ) -> str:
        if value is None:
            return "<missing>"

        try:
            return str(value)
        except Exception:
            return "<unprintable>"

    # ==================================================================
    # Lifecycle
    # ==================================================================

    def closeEvent(self, event) -> None:
        self.bridge.close()

        super().closeEvent(
            event,
        )
