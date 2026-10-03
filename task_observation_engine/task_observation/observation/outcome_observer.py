from __future__ import annotations

from dataclasses import dataclass

from ..models import ObservationSnapshot


@dataclass(frozen=True)
class OutcomeObservation:
    """Derived observations about task outcome."""

    status: str
    completed: bool
    failed: bool
    cancelled: bool

    approval_label: bool | None

    had_tool_failure: bool
    recovered_from_failure: bool


class OutcomeObserver:
    """Derives outcome and recovery observations."""

    def observe(self, snapshot: ObservationSnapshot) -> OutcomeObservation:
        completed = snapshot.status == "completed"
        failed = snapshot.status == "failed"
        cancelled = snapshot.status == "cancelled"

        tool_completed = [
            event for event in snapshot.events if event.name == "tool_completed"
        ]

        had_tool_failure = any(
            event.payload.get("success") is False for event in tool_completed
        )

        recovered_from_failure = self._detect_recovery(snapshot)

        approval_label = self._approval_label(snapshot)

        return OutcomeObservation(
            status=snapshot.status,
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            approval_label=approval_label,
            had_tool_failure=had_tool_failure,
            recovered_from_failure=recovered_from_failure,
        )

    @staticmethod
    def _approval_label(
        snapshot: ObservationSnapshot,
    ) -> bool | None:
        for item in reversed(snapshot.discrete):
            if item.name in {
                "approval_label",
                "approved",
                "human_approved",
            }:
                if item.value is None:
                    return None

                return bool(item.value)

        return None

    @staticmethod
    def _detect_recovery(
        snapshot: ObservationSnapshot,
    ) -> bool:
        failure_seen = False

        for event in snapshot.events:
            if event.name != "tool_completed":
                continue

            if event.payload.get("success") is False:
                failure_seen = True
                continue

            if failure_seen and event.payload.get("success") is True:
                return True

        return False
