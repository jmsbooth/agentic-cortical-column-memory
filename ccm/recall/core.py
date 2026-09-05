"""Deterministic, provenance-bearing recall over structured CCM memory."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable, TYPE_CHECKING

from ccm.schemas.models import Hypothesis, Observation

if TYPE_CHECKING:
    from ccm.memory.store import MemoryStore


_TOKEN = re.compile(r"[a-zA-Z0-9_:-]+")


def _tokens(value: str) -> set[str]:
    return {item.casefold() for item in _TOKEN.findall(value) if len(item) > 1}


@dataclass(frozen=True)
class RecallQuery:
    """A bounded, explicit query against agent memory."""

    query: str
    frame_id: str | None = None
    location: str | None = None
    at_time: str | None = None
    required_object_ids: tuple[str, ...] = ()
    max_items: int = 8
    max_context_tokens: int = 256

    def __post_init__(self) -> None:
        if not self.query:
            raise ValueError("recall queries require a query string")
        if self.max_items < 1 or self.max_context_tokens < 1:
            raise ValueError("recall budgets must be positive")


@dataclass(frozen=True)
class MemoryContext:
    """The bounded memory context delivered to an agent reasoning model."""

    query: str
    observations: tuple[Observation, ...]
    current_state: tuple[Observation, ...]
    supporting_observation_ids: tuple[str, ...]
    unresolved_conflicts: tuple[tuple[str, ...], ...]
    hypotheses: tuple[Hypothesis, ...]
    provenance: tuple[str, ...]
    confidence: float
    context_tokens: int

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["observations"] = [item.to_dict() for item in self.observations]
        result["current_state"] = [item.to_dict() for item in self.current_state]
        result["hypotheses"] = [item.to_dict() for item in self.hypotheses]
        return result

    def to_prompt(self, max_tokens: int | None = None) -> str:
        """Render a bounded, provenance-bearing context for a reasoning model."""

        limit = max_tokens or self.context_tokens or 1
        lines = [f"Memory recall for: {self.query}"]
        for item in self.observations:
            observed = f", observed_at={item.observed_at}" if item.observed_at else ""
            lines.append(
                f"[{item.object_id}] {item.content} "
                f"(source={item.source}, provenance={item.provenance}{observed})"
            )
        if self.unresolved_conflicts:
            lines.append("Unresolved conflicts: " + "; ".join(",".join(group) for group in self.unresolved_conflicts))
        if self.hypotheses:
            lines.append("Candidate hypotheses: " + "; ".join(item.claim for item in self.hypotheses))
        output: list[str] = []
        token_count = 0
        for line in lines:
            next_count = token_count + len(line.split())
            if output and next_count > limit:
                break
            output.append(line)
            token_count = next_count
        return "\n".join(output)


def _conflicts(observations: Iterable[Observation]) -> tuple[tuple[str, ...], ...]:
    by_location: dict[tuple[str, str], list[Observation]] = {}
    for item in observations:
        by_location.setdefault((item.frame_id, item.location), []).append(item)
    return tuple(
        tuple(sorted(item.object_id for item in group))
        for group in by_location.values()
        if len({item.content for item in group}) > 1
    )


def recall(
    store: "MemoryStore",
    query: RecallQuery,
    *,
    current_context: str = "",
    hypotheses: tuple[object, ...] = (),
) -> MemoryContext:
    """Recall relevant observations without mutating or collapsing history."""

    candidates = list(store.all())
    if query.frame_id is not None:
        candidates = [item for item in candidates if item.frame_id == query.frame_id]
    if query.location is not None:
        candidates = [item for item in candidates if item.location == query.location]
    if query.at_time is not None:
        candidates = [
            item for item in candidates
            if (item.valid_from is None or item.valid_from <= query.at_time)
            and (item.valid_to is None or query.at_time < item.valid_to)
        ]

    query_tokens = _tokens(" ".join((query.query, current_context)))
    required = set(query.required_object_ids)

    def score(item: Observation) -> tuple[int, int, int, str]:
        overlap = len(query_tokens & _tokens(f"{item.content} {' '.join(item.relations)}"))
        required_score = 100 if item.object_id in required else 0
        return (required_score + overlap, required_score, item.sequence, item.object_id)

    ranked = sorted(candidates, key=score, reverse=True)
    selected = ranked[: query.max_items]
    current = tuple(
        item for item in store.current(query.frame_id, location=query.location, at_time=query.at_time)
        if item in selected or query.frame_id is None
    ) if query.frame_id is not None else ()
    selected_ids = tuple(item.object_id for item in selected)
    conflicts = _conflicts(selected)
    provenances = tuple(dict.fromkeys(item.provenance for item in selected))
    selected_hypotheses = tuple(item for item in hypotheses if isinstance(item, Hypothesis))
    confidence = min(
        1.0,
        sum(item.confidence for item in selected) / len(selected)
        if selected else 0.0,
    )
    context = MemoryContext(
        query=query.query,
        observations=tuple(selected),
        current_state=current,
        supporting_observation_ids=selected_ids,
        unresolved_conflicts=conflicts,
        hypotheses=selected_hypotheses,
        provenance=provenances,
        confidence=round(confidence, 6),
        context_tokens=0,
    )
    rendered = context.to_prompt(query.max_context_tokens)
    return MemoryContext(
        query=context.query,
        observations=context.observations,
        current_state=context.current_state,
        supporting_observation_ids=context.supporting_observation_ids,
        unresolved_conflicts=context.unresolved_conflicts,
        hypotheses=context.hypotheses,
        provenance=context.provenance,
        confidence=context.confidence,
        context_tokens=len(rendered.split()),
    )


def assemble_context(context: MemoryContext, max_tokens: int = 256) -> str:
    """Assemble only a bounded, auditable representation for model input."""

    if max_tokens < 1:
        raise ValueError("context budget must be positive")
    return context.to_prompt(max_tokens)
