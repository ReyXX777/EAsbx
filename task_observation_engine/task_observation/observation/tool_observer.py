from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from ..models import ObservationSnapshot


@dataclass(frozen=True)
class ToolObservation:
    """Derived observations about tool usage within a task."""

    total_tool_calls: int
    successful_tool_calls: int
    failed_tool_calls: int
    unique_tools: int

    list_directory_count: int
    search_files_count: int
    read_file_count: int
    read_table_count: int
    compute_count: int

    tool_counts: dict[str, int]


class ToolObserver:
    """Derives tool-usage observations from an ObservationSnapshot."""

    def observe(self, snapshot: ObservationSnapshot) -> ToolObservation:
        tool_started = [
            event for event in snapshot.events if event.name == "tool_started"
        ]

        tool_completed = [
            event for event in snapshot.events if event.name == "tool_completed"
        ]

        tool_counts: Counter[str] = Counter()

        for event in tool_started:
            tool_name = event.payload.get("tool_name")

            if tool_name:
                tool_counts[str(tool_name)] += 1

        successful = sum(
            1 for event in tool_completed if event.payload.get("success") is True
        )

        failed = sum(
            1 for event in tool_completed if event.payload.get("success") is False
        )

        return ToolObservation(
            total_tool_calls=len(tool_started),
            successful_tool_calls=successful,
            failed_tool_calls=failed,
            unique_tools=len(tool_counts),
            list_directory_count=tool_counts.get("list_directory", 0),
            search_files_count=tool_counts.get("search_files", 0),
            read_file_count=tool_counts.get("read_file", 0),
            read_table_count=tool_counts.get("read_table", 0),
            compute_count=sum(
                count
                for name, count in tool_counts.items()
                if name.startswith("compute")
            ),
            tool_counts=dict(tool_counts),
        )
