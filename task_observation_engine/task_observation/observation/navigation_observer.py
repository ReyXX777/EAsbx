from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from ..models import ObservationSnapshot


@dataclass(frozen=True)
class NavigationObservation:
    """Derived observations about filesystem navigation."""

    unique_paths: int
    paths_visited: int
    directory_navigation_count: int
    file_access_count: int
    maximum_path_depth: int

    search_count: int
    navigation_reversal_count: int

    visited_paths: tuple[str, ...]


class NavigationObserver:
    """Derives navigation-related observations."""

    def observe(self, snapshot: ObservationSnapshot) -> NavigationObservation:
        traces = [trace for trace in snapshot.traces if trace.path is not None]

        paths = [trace.path for trace in traces if trace.path is not None]

        unique_paths = tuple(dict.fromkeys(paths))

        action_phases = {
            "tool_started",
        }

        directory_navigation_count = sum(
            1
            for trace in traces
            if (trace.phase in action_phases and trace.action == "list_directory")
        )

        file_access_count = sum(
            1
            for trace in traces
            if (
                trace.phase in action_phases
                and trace.action
                in {
                    "read_file",
                    "read_table",
                }
            )
        )

        search_count = sum(
            1
            for trace in traces
            if (trace.phase in action_phases and trace.action == "search_files")
        )
        maximum_path_depth = 0

        for path in unique_paths:
            depth = self._path_depth(path)
            maximum_path_depth = max(maximum_path_depth, depth)

        navigation_reversal_count = self._count_reversals(traces)

        return NavigationObservation(
            unique_paths=len(unique_paths),
            paths_visited=len(paths),
            directory_navigation_count=directory_navigation_count,
            file_access_count=file_access_count,
            maximum_path_depth=maximum_path_depth,
            search_count=search_count,
            navigation_reversal_count=navigation_reversal_count,
            visited_paths=unique_paths,
        )

    @staticmethod
    def _path_depth(path: str) -> int:
        normalized = path.replace("\\", "/").strip("/")

        if not normalized or normalized == ".":
            return 0

        return len(
            [part for part in PurePosixPath(normalized).parts if part not in {".", ""}]
        )

    @staticmethod
    def _count_reversals(traces) -> int:
        paths = [trace.path for trace in traces if trace.path is not None]

        reversals = 0

        for previous, current in zip(paths, paths[1:]):
            if previous == current:
                continue

            previous_parts = previous.replace("\\", "/").strip("/").split("/")
            current_parts = current.replace("\\", "/").strip("/").split("/")

            if (
                len(current_parts) < len(previous_parts)
                and previous_parts[: len(current_parts)] == current_parts
            ):
                reversals += 1

        return reversals
