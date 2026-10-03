from __future__ import annotations

from dataclasses import dataclass

from ..models import ObservationSnapshot
from .navigation_observer import NavigationObservation, NavigationObserver
from .outcome_observer import OutcomeObservation, OutcomeObserver
from .timing_observer import TimingObservation, TimingObserver
from .tool_observer import ToolObservation, ToolObserver


@dataclass(frozen=True)
class DerivedObservationFeatures:
    """Complete derived observation set for one task."""

    tool: ToolObservation
    navigation: NavigationObservation
    timing: TimingObservation
    outcome: OutcomeObservation

    def continuous_features(self) -> dict[str, float]:
        """Return numerical features suitable for the math layer."""

        values: dict[str, float] = {
            "total_tool_calls": float(self.tool.total_tool_calls),
            "successful_tool_calls": float(self.tool.successful_tool_calls),
            "failed_tool_calls": float(self.tool.failed_tool_calls),
            "unique_tools": float(self.tool.unique_tools),
            "list_directory_count": float(self.tool.list_directory_count),
            "search_files_count": float(self.tool.search_files_count),
            "read_file_count": float(self.tool.read_file_count),
            "read_table_count": float(self.tool.read_table_count),
            "compute_count": float(self.tool.compute_count),
            "unique_paths": float(self.navigation.unique_paths),
            "paths_visited": float(self.navigation.paths_visited),
            "directory_navigation_count": float(
                self.navigation.directory_navigation_count
            ),
            "file_access_count": float(self.navigation.file_access_count),
            "maximum_path_depth": float(self.navigation.maximum_path_depth),
            "search_count": float(self.navigation.search_count),
            "navigation_reversal_count": float(
                self.navigation.navigation_reversal_count
            ),
        }

        if self.timing.task_duration_seconds is not None:
            values["task_duration_seconds"] = self.timing.task_duration_seconds

        if self.timing.average_tool_duration_seconds is not None:
            values["average_tool_duration_seconds"] = (
                self.timing.average_tool_duration_seconds
            )

        if self.timing.minimum_tool_duration_seconds is not None:
            values["minimum_tool_duration_seconds"] = (
                self.timing.minimum_tool_duration_seconds
            )

        if self.timing.maximum_tool_duration_seconds is not None:
            values["maximum_tool_duration_seconds"] = (
                self.timing.maximum_tool_duration_seconds
            )

        return values

    def discrete_features(self) -> dict[str, str | bool]:
        """Return categorical/state features."""

        values: dict[str, str | bool] = {
            "task_status": self.outcome.status,
            "task_completed": self.outcome.completed,
            "task_failed": self.outcome.failed,
            "task_cancelled": self.outcome.cancelled,
            "had_tool_failure": self.outcome.had_tool_failure,
            "recovered_from_failure": (self.outcome.recovered_from_failure),
            "used_search": self.tool.search_files_count > 0,
            "used_computation": self.tool.compute_count > 0,
            "used_file_read": (
                self.tool.read_file_count > 0 or self.tool.read_table_count > 0
            ),
        }

        if self.outcome.approval_label is not None:
            values["approval_label"] = self.outcome.approval_label

        return values


class FeatureDeriver:
    """Coordinates all independent observation derivations."""

    def __init__(
        self,
        *,
        tool_observer: ToolObserver | None = None,
        navigation_observer: NavigationObserver | None = None,
        timing_observer: TimingObserver | None = None,
        outcome_observer: OutcomeObserver | None = None,
    ) -> None:
        self.tool_observer = tool_observer or ToolObserver()
        self.navigation_observer = navigation_observer or NavigationObserver()
        self.timing_observer = timing_observer or TimingObserver()
        self.outcome_observer = outcome_observer or OutcomeObserver()

    def derive(
        self,
        snapshot: ObservationSnapshot,
    ) -> DerivedObservationFeatures:
        return DerivedObservationFeatures(
            tool=self.tool_observer.observe(snapshot),
            navigation=self.navigation_observer.observe(snapshot),
            timing=self.timing_observer.observe(snapshot),
            outcome=self.outcome_observer.observe(snapshot),
        )
