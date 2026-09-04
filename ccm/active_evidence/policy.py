"""Information-seeking action selection."""

from __future__ import annotations

from typing import Iterable, Optional

from ccm.schemas.models import EvidenceAction, Hypothesis


class ActiveEvidencePolicy:
    def select(
        self,
        hypotheses: Iterable[Hypothesis],
        actions: Iterable[EvidenceAction],
        *,
        used_action_ids: set[str],
        budget_remaining: float,
    ) -> Optional[EvidenceAction]:
        """Choose the available action with greatest expected gain per cost."""

        hypothesis_ids = {item.hypothesis_id for item in hypotheses}
        candidates = [
            action
            for action in actions
            if action.action_id not in used_action_ids
            and action.cost <= budget_remaining
            and hypothesis_ids.intersection(action.target_hypothesis_ids)
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (
                item.expected_information_gain / item.cost,
                item.expected_information_gain,
                item.action_id,
            ),
        )
