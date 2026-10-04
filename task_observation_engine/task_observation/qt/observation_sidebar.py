from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ObservationSidebar(QWidget):
    """Navigation, search, filtering and session selection."""

    session_selected = Signal(str)
    filters_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._all_sessions: list[dict] = []

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        root.setSpacing(8)

        self.live_label = QLabel(
            "🔴 Live",
        )

        self.live_label.setStyleSheet("font-weight: bold;")

        root.addWidget(
            self.live_label,
        )

        self.search_field = QLineEdit()

        self.search_field.setPlaceholderText(
            "Search sessions...",
        )

        root.addWidget(
            self.search_field,
        )

        filters_label = QLabel(
            "FILTERS",
        )

        filters_label.setStyleSheet("font-weight: bold;")

        root.addWidget(
            filters_label,
        )

        # ----------------------------------------------------------
        # Status
        # ----------------------------------------------------------

        status_group = QGroupBox(
            "Status",
        )

        status_layout = QVBoxLayout(
            status_group,
        )

        self.status_selector = QComboBox()

        self.status_selector.addItems(
            [
                "All",
                "Completed",
                "Running",
                "Failed",
                "Cancelled",
            ]
        )

        status_layout.addWidget(
            self.status_selector,
        )

        root.addWidget(
            status_group,
        )

        # ----------------------------------------------------------
        # Family
        # ----------------------------------------------------------

        family_group = QGroupBox(
            "Family",
        )

        family_layout = QVBoxLayout(
            family_group,
        )

        self.family_selector = QComboBox()

        self.family_selector.addItem(
            "All",
        )

        family_layout.addWidget(
            self.family_selector,
        )

        root.addWidget(
            family_group,
        )

        # ----------------------------------------------------------
        # Sessions
        # ----------------------------------------------------------

        sessions_label = QLabel(
            "SESSIONS",
        )

        sessions_label.setStyleSheet("font-weight: bold;")

        root.addWidget(
            sessions_label,
        )

        self.session_list = QListWidget()

        root.addWidget(
            self.session_list,
            1,
        )

    def _connect_signals(self) -> None:
        self.search_field.textChanged.connect(
            self._apply_filters,
        )

        self.status_selector.currentTextChanged.connect(
            self._apply_filters,
        )

        self.family_selector.currentTextChanged.connect(
            self._apply_filters,
        )

        self.session_list.itemClicked.connect(
            self._session_clicked,
        )

    def set_live(
        self,
        live: bool,
    ) -> None:
        if live:
            self.live_label.setText(
                "🔴 Live",
            )
        else:
            self.live_label.setText(
                "⚪ No active session",
            )

    def set_sessions(
        self,
        sessions: Iterable[dict],
    ) -> None:
        self._all_sessions = [dict(session) for session in sessions]

        self._rebuild_family_selector()
        self._apply_filters()

    def _rebuild_family_selector(self) -> None:
        current = self.family_selector.currentText()

        families = sorted(
            {
                str(session.get("family", ""))
                for session in self._all_sessions
                if session.get("family")
            }
        )

        self.family_selector.blockSignals(
            True,
        )

        try:
            self.family_selector.clear()
            self.family_selector.addItem("All")

            for family in families:
                self.family_selector.addItem(
                    family,
                )

            if current in families:
                self.family_selector.setCurrentText(
                    current,
                )
            else:
                self.family_selector.setCurrentText(
                    "All",
                )

        finally:
            self.family_selector.blockSignals(
                False,
            )

    def _apply_filters(self) -> None:
        search = self.search_field.text().strip().lower()

        status = self.status_selector.currentText().lower()

        family = self.family_selector.currentText()

        self.session_list.clear()

        for session in self._all_sessions:
            session_id = str(session.get("session_id", ""))

            session_family = str(session.get("family", ""))

            session_status = str(session.get("status", "")).lower()

            searchable = (
                f"{session_id} " f"{session_family} " f"{session_status}"
            ).lower()

            if search and search not in searchable:
                continue

            if status != "all" and session_status != status:
                continue

            if family != "All" and session_family != family:
                continue

            item = QListWidgetItem()

            item.setText(
                self._format_session_label(
                    session,
                )
            )

            item.setData(
                Qt.UserRole,
                session_id,
            )

            self.session_list.addItem(
                item,
            )

        self.filters_changed.emit()

    def _session_clicked(
        self,
        item: QListWidgetItem,
    ) -> None:
        session_id = item.data(
            Qt.UserRole,
        )

        if session_id:
            self.session_selected.emit(
                str(session_id),
            )

    @staticmethod
    def _format_session_label(
        session: dict,
    ) -> str:
        family = str(session.get("family", "unknown"))

        status = str(session.get("status", "unknown"))

        session_id = str(session.get("session_id", ""))

        return f"{family}  •  " f"{status}  •  " f"{session_id}"
