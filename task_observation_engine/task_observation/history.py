from __future__ import annotations

from dataclasses import dataclass
import json
import os

from .models import ObservationSnapshot
from .storage.serialization import snapshot_from_dict


@dataclass(frozen=True)
class ObservationSeriesPoint:
    """One historical continuous-observation value."""

    session_id: str
    timestamp: str
    value: float


class ObservationHistory:
    """Build a tolerant historical index from persisted observations.

    Each task/session is persisted independently as JSON.

    This class reads those files and exposes continuous observations as
    cross-session time series for the observation monitor.

    Design goals:

    - Missing files do not stop the application.
    - Missing JSON fields do not stop aggregation.
    - Missing continuous observations are ignored.
    - Missing observation values are ignored.
    - Invalid numeric values are ignored.
    - Malformed JSON is ignored.
    - Invalid individual snapshots are ignored.
    - One bad historical session never prevents other sessions from
      appearing in the monitor.
    - The persisted JSON files remain the source of truth.
    """

    def __init__(
        self,
        storage_root: str,
    ) -> None:
        self.storage_root = os.path.abspath(
            storage_root,
        )

        self._snapshots: list[ObservationSnapshot] = []

        self._series: dict[
            str,
            list[ObservationSeriesPoint],
        ] = {}

        self.refresh()





    def refresh(self) -> None:
        """Reload all readable observation JSON files."""

        snapshots: list[ObservationSnapshot] = []

        if not os.path.isdir(self.storage_root):
            self._snapshots = []
            self._series = {}
            return

        try:
            filenames = os.listdir(
                self.storage_root,
            )
        except OSError:
            self._snapshots = []
            self._series = {}
            return

        for filename in sorted(filenames):
            if not filename.lower().endswith(".json"):
                continue

            path = os.path.join(
                self.storage_root,
                filename,
            )

            if not os.path.isfile(path):
                continue

            snapshot = self._load_snapshot(
                path,
            )

            if snapshot is None:
                continue

            snapshots.append(
                snapshot,
            )

        snapshots.sort(
            key=self._snapshot_sort_key,
        )

        self._snapshots = snapshots

        self._rebuild_series()

    def add_snapshot(
        self,
        snapshot: ObservationSnapshot,
    ) -> None:
        """Add or replace one snapshot in the historical index."""

        if snapshot is None:
            return

        session_id = self._session_id(
            snapshot,
        )

        if session_id:
            for index, existing in enumerate(
                self._snapshots,
            ):
                if self._session_id(existing) == session_id:
                    self._snapshots[index] = snapshot
                    break
            else:
                self._snapshots.append(
                    snapshot,
                )
        else:
            self._snapshots.append(
                snapshot,
            )

        self._snapshots.sort(
            key=self._snapshot_sort_key,
        )

        self._rebuild_series()

    def snapshots(
        self,
    ) -> tuple[ObservationSnapshot, ...]:
        """Return all successfully loaded snapshots."""

        return tuple(
            self._snapshots,
        )

    def feature_names(
        self,
    ) -> tuple[str, ...]:
        """Return all continuous feature names."""

        return tuple(
            sorted(
                self._series.keys(),
            ),
        )

    def get_series(
        self,
        name: str,
    ) -> tuple[ObservationSeriesPoint, ...]:
        """Return historical points for one feature."""

        if not name:
            return ()

        return tuple(
            self._series.get(
                name,
                (),
            ),
        )

    def get_values(
        self,
        name: str,
    ) -> list[float]:
        """Return only numeric values for one feature."""

        return [
            point.value
            for point in self._series.get(
                name,
                (),
            )
        ]





    @staticmethod
    def _load_snapshot(
        path: str,
    ) -> ObservationSnapshot | None:
        """Safely load one observation JSON file.

        Any problem with this file is isolated to this file.
        """

        try:
            with open(
                path,
                "r",
                encoding="utf-8",
            ) as handle:
                data = json.load(
                    handle,
                )

        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return None

        if not isinstance(
            data,
            dict,
        ):
            return None

        try:
            return snapshot_from_dict(
                data,
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
        ):
            return None





    def _rebuild_series(self) -> None:
        """Rebuild the cross-session continuous feature index."""

        series: dict[
            str,
            list[ObservationSeriesPoint],
        ] = {}

        for snapshot in self._snapshots:
            session_id = self._session_id(
                snapshot,
            )

            continuous = getattr(
                snapshot,
                "continuous",
                (),
            )

            if not continuous:
                continue

            for observation in continuous:
                name = getattr(
                    observation,
                    "name",
                    None,
                )

                if not isinstance(
                    name,
                    str,
                ):
                    continue

                name = name.strip()

                if not name:
                    continue

                raw_value = getattr(
                    observation,
                    "value",
                    None,
                )

                if raw_value is None:
                    continue

                try:
                    value = float(
                        raw_value,
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                timestamp = getattr(
                    observation,
                    "timestamp",
                    None,
                )

                if not isinstance(
                    timestamp,
                    str,
                ):
                    timestamp = ""

                series.setdefault(
                    name,
                    [],
                ).append(
                    ObservationSeriesPoint(
                        session_id=session_id,
                        timestamp=timestamp,
                        value=value,
                    ),
                )

        for points in series.values():
            points.sort(
                key=lambda point: (
                    point.timestamp,
                    point.session_id,
                ),
            )

        self._series = series





    @staticmethod
    def _session_id(
        snapshot: ObservationSnapshot,
    ) -> str:
        identity = getattr(
            snapshot,
            "identity",
            None,
        )

        session_id = getattr(
            identity,
            "session_id",
            "",
        )

        if not isinstance(
            session_id,
            str,
        ):
            return ""

        return session_id

    @classmethod
    def _snapshot_sort_key(
        cls,
        snapshot: ObservationSnapshot,
    ) -> tuple[str, str]:
        started_at = getattr(
            snapshot,
            "started_at",
            "",
        )

        if not isinstance(
            started_at,
            str,
        ):
            started_at = ""

        return (
            started_at,
            cls._session_id(snapshot),
        )
