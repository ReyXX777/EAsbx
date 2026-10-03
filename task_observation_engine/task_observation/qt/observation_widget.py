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

from ..models import ObservationSnapshot
from ..replay import ReplayAPI
from .observation_bridge import ObservationBridge
from .observation_plot import ObservationPlot


class ObservationWidget(QWidget):
    """Qt visualization surface for task observations.

    Responsibilities:

    - display live/final observation snapshots
    - display discrete features
    - display continuous features
    - display event/trace information when present
    - load persisted sessions through ReplayAPI

    It does not mutate the observation session.
    """

    def __init__(
        self,
        storage_root,
        parent=None,
    ):
        super().__init__(parent)

        self.storage_root = storage_root

        self.bridge = ObservationBridge(
            storage_root,
            self,
        )

        self._snapshot = None

        self._build_ui()
        self._connect_bridge()

        self.refresh_history()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        root.setSpacing(6)

        # -----------------------------------------------------
        # Toolbar
        # -----------------------------------------------------

        toolbar = QHBoxLayout()

        self.family_field = QComboBox()
        self.family_field.setEditable(True)
        self.family_field.setPlaceholderText("Task family")

        start_button = QPushButton(
            "Start Observation",
        )

        finish_button = QPushButton(
            "Finish",
        )

        refresh_button = QPushButton(
            "Refresh History",
        )

        start_button.clicked.connect(
            self._start_task,
        )

        finish_button.clicked.connect(
            self._finish_task,
        )

        refresh_button.clicked.connect(
            self.refresh_history,
        )

        toolbar.addWidget(
            QLabel("Family:"),
        )

        toolbar.addWidget(
            self.family_field,
            1,
        )

        toolbar.addWidget(
            start_button,
        )

        toolbar.addWidget(
            finish_button,
        )

        toolbar.addWidget(
            refresh_button,
        )

        root.addLayout(
            toolbar,
        )

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        self.status_label = QLabel(
            "No active observation.",
        )

        root.addWidget(
            self.status_label,
        )

        # -----------------------------------------------------
        # Main splitter
        # -----------------------------------------------------

        splitter = QSplitter(
            Qt.Horizontal,
        )

        # -----------------------------------------------------
        # History
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Right side
        # -----------------------------------------------------

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

        # Metadata

        metadata_group = QGroupBox(
            "Session",
        )

        metadata_layout = QFormLayout(
            metadata_group,
        )

        self.session_id_label = QLabel("-")
        self.family_label = QLabel("-")
        self.session_status_label = QLabel("-")

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

        right_layout.addWidget(
            metadata_group,
        )

        # -----------------------------------------------------
        # Feature selector
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Plot
        # -----------------------------------------------------

        self.plot = ObservationPlot()

        right_layout.addWidget(
            self.plot,
            2,
        )

        # -----------------------------------------------------
        # Bottom splitter
        # -----------------------------------------------------

        lower_splitter = QSplitter(
            Qt.Vertical,
        )

        # Discrete

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

        # Events/traces

        event_group = QGroupBox(
            "Events / Trace",
        )

        event_layout = QVBoxLayout(
            event_group,
        )

        self.event_table = QTableWidget()

        self.event_table.setColumnCount(
            3,
        )

        self.event_table.setHorizontalHeaderLabels(
            [
                "Type",
                "Name",
                "Value",
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

    # ---------------------------------------------------------
    # Bridge
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Commands
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Worker events
    # ---------------------------------------------------------

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

    def _on_task_finished(
        self,
        snapshot: object,
    ) -> None:
        self.status_label.setText(
            "Observation completed.",
        )

        self._display_snapshot(
            snapshot,
        )

        self.refresh_history()

    def _on_error(
        self,
        message: str,
    ) -> None:
        self.status_label.setText(f"Observation error: {message}")

    # ---------------------------------------------------------
    # Snapshot display
    # ---------------------------------------------------------

    def _display_snapshot(
        self,
        snapshot: object,
    ) -> None:
        if snapshot is None:
            return

        self._snapshot = snapshot

        identity = getattr(
            snapshot,
            "identity",
            None,
        )

        if identity is not None:
            self.session_id_label.setText(
                str(
                    getattr(
                        identity,
                        "session_id",
                        "-",
                    )
                )
            )

            self.family_label.setText(
                str(
                    getattr(
                        identity,
                        "family_key",
                        getattr(
                            identity,
                            "family",
                            "-",
                        ),
                    )
                )
            )

        self.session_status_label.setText(
            str(
                getattr(
                    snapshot,
                    "status",
                    "-",
                )
            )
        )

        self._display_discrete(
            getattr(
                snapshot,
                "discrete",
                (),
            )
        )

        self._display_continuous(
            getattr(
                snapshot,
                "continuous",
                (),
            )
        )

        self._display_events(
            snapshot,
        )

    # ---------------------------------------------------------
    # Discrete
    # ---------------------------------------------------------

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
                    str(
                        getattr(
                            observation,
                            "name",
                            "",
                        )
                    )
                ),
            )

            self.discrete_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    self._safe_text(
                        getattr(
                            observation,
                            "value",
                            None,
                        )
                    )
                ),
            )

        self.discrete_table.resizeColumnsToContents()

    # ---------------------------------------------------------
    # Continuous
    # ---------------------------------------------------------

    def _display_continuous(
        self,
        observations,
    ) -> None:
        self.feature_selector.blockSignals(
            True,
        )

        current = self.feature_selector.currentText()

        self.feature_selector.clear()

        names = []

        for observation in observations:
            name = str(
                getattr(
                    observation,
                    "name",
                    "",
                )
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
        if self._snapshot is None:
            return

        self._render_selected_continuous(
            getattr(
                self._snapshot,
                "continuous",
                (),
            )
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

            name = str(
                getattr(
                    observation,
                    "name",
                    "",
                )
            )

            if name != selected:
                continue

            value = getattr(
                observation,
                "value",
                None,
            )

            try:
                if value is not None:
                    values.append(float(value))
            except (
                TypeError,
                ValueError,
            ):
                continue

        self.plot.set_data(
            values,
            selected,
        )

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def _display_events(
        self,
        snapshot,
    ) -> None:
        self.event_table.setRowCount(
            0,
        )

        collections = []

        for attribute_name in (
            "events",
            "trace",
            "traces",
            "event_trace",
        ):
            value = getattr(
                snapshot,
                attribute_name,
                None,
            )

            if value:
                collections.append(value)

        for collection in collections:

            for event in collection:

                row = self.event_table.rowCount()

                self.event_table.insertRow(
                    row,
                )

                event_type = getattr(
                    event,
                    "event_type",
                    getattr(
                        event,
                        "type",
                        "",
                    ),
                )

                name = getattr(
                    event,
                    "name",
                    getattr(
                        event,
                        "operation",
                        "",
                    ),
                )

                value = getattr(
                    event,
                    "value",
                    getattr(
                        event,
                        "payload",
                        "",
                    ),
                )

                self.event_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(self._safe_text(event_type)),
                )

                self.event_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(self._safe_text(name)),
                )

                self.event_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(self._safe_text(value)),
                )

        self.event_table.resizeColumnsToContents()

    # ---------------------------------------------------------
    # History / Replay
    # ---------------------------------------------------------

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
                session_id,
            )

            self._display_snapshot(
                snapshot,
            )

            self.status_label.setText(f"Loaded session: {session_id}")

        except Exception as exc:
            self.status_label.setText(f"Replay error: {exc}")

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def closeEvent(self, event) -> None:
        self.bridge.close()

        super().closeEvent(
            event,
        )
