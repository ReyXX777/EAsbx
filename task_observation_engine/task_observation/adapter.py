from __future__ import annotations

from .models import ObservationSnapshot
from mathematical_approval import ActionObservation, FeatureVector, TaskFamily


class MathematicalApprovalAdapter:
    """One-way bridge from collected observations to the existing math package.

    The collector itself never imports or depends on mathematical_approval.
    This adapter is intentionally the only coupling point.
    """

    def __init__(self, continuous_feature_names: tuple[str, ...]) -> None:
        self.continuous_feature_names = continuous_feature_names

    def to_observation(self, snapshot: ObservationSnapshot) -> ActionObservation:
        label = self._approval_label(snapshot)
        family = TaskFamily(snapshot.identity.family_key)
        vector = FeatureVector.from_sequence(snapshot.to_feature_vector(self.continuous_feature_names))
        return ActionObservation(family=family, features=vector, approved=label)

    @staticmethod
    def _approval_label(snapshot: ObservationSnapshot) -> bool:
        for item in reversed(snapshot.discrete):
            if item.name in {"approval_label", "approved", "human_approved"}:
                return bool(item.value) if item.value is not None else False
        return False
