"""Reference-frame validation and state transition operations."""

from __future__ import annotations

from dataclasses import replace

from ccm.schemas.models import Observation, ReferenceFrame, Transition


class FrameError(ValueError):
    """Raised when a transition or observation violates a frame contract."""


class ReferenceFrameGraph:
    def __init__(self, frame: ReferenceFrame):
        self.frame = frame
        self._transitions = {(item.source, item.action): item.target for item in frame.transitions}
        self._observation_ids: dict[str, list[str]] = {
            state: list(ids) for state, ids in frame.observations_by_state
        }

    def transition(self, action: str) -> ReferenceFrame:
        key = (self.frame.state, action)
        if key not in self._transitions:
            raise FrameError(f"invalid transition {action!r} from {self.frame.state!r}")
        target = self._transitions[key]
        self.frame = replace(self.frame, state=target)
        return self.frame

    def validate_observation(self, observation: Observation) -> None:
        if observation.frame_id != self.frame.frame_id:
            raise FrameError("observation belongs to a different reference frame")
        valid_states = {self.frame.origin, self.frame.state}
        valid_states.update(t.source for t in self.frame.transitions)
        valid_states.update(t.target for t in self.frame.transitions)
        if observation.location not in valid_states:
            raise FrameError(f"unknown location {observation.location!r} in frame")

    def attach_observation(self, observation: Observation) -> None:
        self.validate_observation(observation)
        self._observation_ids.setdefault(observation.location, []).append(observation.object_id)

    def predict_next_location(self, action: str) -> str:
        key = (self.frame.state, action)
        if key not in self._transitions:
            raise FrameError(f"cannot predict from state {self.frame.state!r} using {action!r}")
        return self._transitions[key]
