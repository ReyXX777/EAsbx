from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..models import ObservationSnapshot


@dataclass(frozen=True)
class TimingObservation:
    """Derived timing information."""

    task_duration_seconds: float | None
    average_tool_duration_seconds: float | None
    minimum_tool_duration_seconds: float | None
    maximum_tool_duration_seconds: float | None


class TimingObserver:
    """Derives task and tool timing from event timestamps."""

    def observe(self, snapshot: ObservationSnapshot) -> TimingObservation:
        task_duration = self._duration(
            snapshot.started_at,
            snapshot.finished_at,
        )

        started: dict[tuple[str, str | None], datetime] = {}
        durations: list[float] = []

        for event in snapshot.events:
            tool_name = event.payload.get("tool_name")
            path = event.payload.get("path")

            key = (str(tool_name), path)

            if event.name == "tool_started" and tool_name:
                started[key] = self._parse(event.timestamp)

            elif event.name == "tool_completed" and tool_name:
                start = started.pop(key, None)

                if start is not None:
                    end = self._parse(event.timestamp)
                    duration = (end - start).total_seconds()

                    if duration >= 0:
                        durations.append(duration)

        return TimingObservation(
            task_duration_seconds=task_duration,
            average_tool_duration_seconds=(
                sum(durations) / len(durations) if durations else None
            ),
            minimum_tool_duration_seconds=(min(durations) if durations else None),
            maximum_tool_duration_seconds=(max(durations) if durations else None),
        )

    @staticmethod
    def _parse(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @classmethod
    def _duration(
        cls,
        started_at: str | None,
        finished_at: str | None,
    ) -> float | None:
        if not started_at or not finished_at:
            return None

        duration = (cls._parse(finished_at) - cls._parse(started_at)).total_seconds()

        return duration if duration >= 0 else None
