"""The inspectable CCM column interface."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional

from ccm.schemas.models import (
    ColumnState,
    EvidenceAction,
    Hypothesis,
    Observation,
    ReferenceFrame,
    Vote,
)


class Column:
    """A local model plus local state, not a synonym for an entire agent.

    The model adapter is intentionally outside this class.  This lets a real
    local or hosted model implement proposal generation while the state and
    communication contract remain testable without credentials.
    """

    def __init__(self, column_id: str, frame: ReferenceFrame, specialization: str):
        if not column_id or not specialization:
            raise ValueError("column id and specialization are required")
        self.column_id = column_id
        self.frame = frame
        self.specialization = specialization
        self._observations: dict[str, Observation] = {}
        self._hypotheses: dict[str, Hypothesis] = {}
        self._peers: dict[str, ColumnState] = {}
        self._requested_action: Optional[str] = None

    def observe(self, observation: Observation) -> None:
        if observation.frame_id != self.frame.frame_id:
            raise ValueError("column cannot observe an observation from another frame")
        self._observations[observation.object_id] = observation

    def update_hypotheses(self, hypotheses: Iterable[Hypothesis]) -> None:
        for hypothesis in hypotheses:
            if hypothesis.frame_id != self.frame.frame_id:
                raise ValueError("hypothesis frame does not match column frame")
            self._hypotheses[hypothesis.hypothesis_id] = hypothesis
            self._requested_action = hypothesis.requested_action or self._requested_action

    def propose_action(self, actions: Iterable[EvidenceAction]) -> Optional[EvidenceAction]:
        candidates = [item for item in actions if item.action_id == self._requested_action]
        if candidates:
            return candidates[0]
        return None

    def emit_state(self) -> ColumnState:
        return ColumnState(
            column_id=self.column_id,
            frame_id=self.frame.frame_id,
            specialization=self.specialization,
            observation_ids=tuple(sorted(self._observations)),
            hypotheses=tuple(self._hypotheses.values()),
            peer_column_ids=tuple(sorted(self._peers)),
            requested_action=self._requested_action,
        )

    def receive_peer_state(self, state: ColumnState) -> None:
        if state.column_id == self.column_id:
            raise ValueError("a column cannot receive its own peer state")
        if state.frame_id != self.frame.frame_id:
            raise ValueError("peer state frame does not match column frame")
        self._peers[state.column_id] = state

    def vote(self) -> Optional[Vote]:
        if not self._hypotheses:
            return None
        hypothesis = max(
            self._hypotheses.values(), key=lambda item: (item.confidence, item.hypothesis_id)
        )
        return Vote(
            vote_id=f"{self.column_id}:{hypothesis.hypothesis_id}",
            column_id=self.column_id,
            hypothesis_id=hypothesis.hypothesis_id,
            hypothesis=hypothesis,
            confidence=hypothesis.confidence,
        )

    def commit(self, status: str) -> None:
        if status not in {"committed", "abstained", "unresolved"}:
            raise ValueError("invalid commit status")
        self._hypotheses = {
            key: replace(value, status=status) for key, value in self._hypotheses.items()
        }
