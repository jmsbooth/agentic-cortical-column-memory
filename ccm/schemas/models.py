"""Stable, JSON-serializable contracts shared by CCM components.

These contracts intentionally keep observations, hypotheses, and votes
separate.  A model-generated hypothesis is never silently promoted to an
external observation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Optional


def _bounded_probability(value: float, field_name: str) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be finite and between 0 and 1")


@dataclass(frozen=True)
class Transition:
    action: str
    source: str
    target: str

    def __post_init__(self) -> None:
        if not self.action or not self.source or not self.target:
            raise ValueError("a transition requires action, source, and target")


@dataclass(frozen=True)
class ReferenceFrame:
    """A navigable conceptual or physical state space.

    ``location`` is represented by a stable application-level state key.  The
    frame is not an agent persona or namespace: it has explicit transitions,
    observations at states, and a prediction boundary.
    """

    frame_id: str
    kind: str
    origin: str
    state: str
    transitions: tuple[Transition, ...] = ()
    observations_by_state: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        if not self.frame_id or not self.kind or not self.origin or not self.state:
            raise ValueError("a reference frame requires id, kind, origin, and state")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Observation:
    """An append-only observation with provenance and validation state."""

    object_id: str
    content: str
    frame_id: str
    location: str
    source: str
    sequence: int
    confidence: float
    provenance: str
    kind: str = "external"
    validation_state: str = "unvalidated"
    relations: tuple[str, ...] = ()
    embedding: Optional[tuple[float, ...]] = None

    def __post_init__(self) -> None:
        if not self.object_id or not self.content or not self.frame_id or not self.location:
            raise ValueError("observation identity, content, frame, and location are required")
        if not self.source or not self.provenance:
            raise ValueError("observations require source and provenance")
        if self.sequence < 0:
            raise ValueError("observation sequence cannot be negative")
        _bounded_probability(self.confidence, "observation confidence")
        if self.kind == "external" and self.source.startswith("model:"):
            raise ValueError("model-generated information cannot be an external observation")
        if self.embedding is not None and not all(isfinite(v) for v in self.embedding):
            raise ValueError("embedding values must be finite")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    claim: str
    frame_id: str
    location: str
    evidence_ids: tuple[str, ...]
    provenance: str
    confidence: float
    uncertainty: float
    requested_action: Optional[str] = None
    status: str = "open"

    def __post_init__(self) -> None:
        if not self.hypothesis_id or not self.claim or not self.frame_id or not self.location:
            raise ValueError("hypotheses require identity, claim, frame, and location")
        if not self.provenance:
            raise ValueError("hypotheses require provenance")
        _bounded_probability(self.confidence, "hypothesis confidence")
        _bounded_probability(self.uncertainty, "hypothesis uncertainty")
        if self.status not in {"open", "committed", "abstained", "unresolved"}:
            raise ValueError(f"invalid hypothesis status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Vote:
    vote_id: str
    column_id: str
    hypothesis_id: str
    hypothesis: Hypothesis
    confidence: float
    rationale_type: str = "structured_state"

    def __post_init__(self) -> None:
        if not self.vote_id or not self.column_id or not self.hypothesis_id:
            raise ValueError("votes require ids")
        if self.hypothesis.hypothesis_id != self.hypothesis_id:
            raise ValueError("vote must reference the supplied hypothesis")
        _bounded_probability(self.confidence, "vote confidence")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceAction:
    action_id: str
    description: str
    target_hypothesis_ids: tuple[str, ...]
    observation: Observation
    expected_information_gain: float
    cost: float = 1.0
    tool_name: str = "synthetic_observer"

    def __post_init__(self) -> None:
        if not self.action_id or not self.description or not self.tool_name:
            raise ValueError("evidence actions require identity, description, and tool")
        if not self.target_hypothesis_ids:
            raise ValueError("evidence actions must target at least one hypothesis")
        if self.expected_information_gain < 0 or self.cost <= 0:
            raise ValueError("information gain must be non-negative and cost must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    observation_id: str
    accepted: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ColumnState:
    column_id: str
    frame_id: str
    specialization: str
    observation_ids: tuple[str, ...]
    hypotheses: tuple[Hypothesis, ...]
    peer_column_ids: tuple[str, ...]
    requested_action: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
