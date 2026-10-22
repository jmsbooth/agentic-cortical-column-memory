"""Append-only in-memory CCM history and explicit current-state interpretation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from ccm.schemas.models import Observation

if TYPE_CHECKING:
    from ccm.recall.core import MemoryContext, RecallQuery


class MemoryConflict(ValueError):
    """Raised for identity reuse or invalid memory mutation."""


@dataclass(frozen=True)
class MemoryOperation:
    operation: str
    object_id: str
    sequence: int


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise MemoryConflict(f"invalid timestamp: {value!r}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MemoryConflict("naive timestamps are not admissible")
    return parsed.astimezone(timezone.utc)


class MemoryStore:
    """Stores immutable observations and records retrieval/write provenance.

    Unsuperseded contradictory observations remain available. A supersession
    without an effective time affects the present but does not rewrite a
    point-in-time historical query when its activation time is unknown.
    """

    def __init__(self) -> None:
        self._objects: dict[str, Observation] = {}
        self._operations: list[MemoryOperation] = []
        self._superseded_by: dict[str, str] = {}
        self._supersession_effective: dict[str, str | None] = {}
        self._supersession_recorded: dict[str, str] = {}

    def write(self, observation: Observation) -> None:
        if observation.object_id in self._objects:
            raise MemoryConflict(f"memory object already exists: {observation.object_id}")
        self._objects[observation.object_id] = observation
        self._operations.append(MemoryOperation("write", observation.object_id, observation.sequence))

    def supersede(self, observation_id: str, replacement_id: str, *, effective_at: str | None = None, recorded_at: str | None = None) -> None:
        if observation_id not in self._objects or replacement_id not in self._objects:
            raise MemoryConflict("supersession requires two stored observations")
        if observation_id == replacement_id:
            raise MemoryConflict("an observation cannot supersede itself")
        if observation_id in self._superseded_by:
            raise MemoryConflict(f"observation already superseded: {observation_id}")
        old, replacement = self._objects[observation_id], self._objects[replacement_id]
        if (old.frame_id, old.location) != (replacement.frame_id, replacement.location):
            raise MemoryConflict("supersession requires the same frame and location")
        effective = _parse_time(effective_at or replacement.valid_from or replacement.observed_at)
        old_start = _parse_time(old.valid_from)
        if effective is not None and old_start is not None and effective < old_start:
            raise MemoryConflict("supersession predates the original state")
        node = replacement_id
        seen = {observation_id}
        while node in self._superseded_by:
            if node in seen:
                raise MemoryConflict("supersession cycle")
            seen.add(node)
            node = self._superseded_by[node]
        if node == observation_id:
            raise MemoryConflict("supersession cycle")
        self._superseded_by[observation_id] = replacement_id
        self._supersession_effective[observation_id] = effective.isoformat() if effective is not None else None
        self._supersession_recorded[observation_id] = (_parse_time(recorded_at) or datetime.now(timezone.utc)).isoformat()
        self._operations.append(MemoryOperation("supersede", observation_id, replacement.sequence))

    def get(self, object_id: str) -> Observation:
        return self._objects[object_id]

    def retrieve(
        self, frame_id: str, location: Optional[str] = None, limit: Optional[int] = None
    ) -> tuple[Observation, ...]:
        values = [item for item in self._objects.values() if item.frame_id == frame_id]
        if location is not None:
            values = [item for item in values if item.location == location]
        values.sort(key=lambda item: (item.sequence, item.object_id))
        if limit is not None:
            if limit < 0:
                raise MemoryConflict("negative memory limit")
            values = values[:limit]
        for item in values:
            self._operations.append(MemoryOperation("retrieve", item.object_id, item.sequence))
        return tuple(values)

    def historical(
        self,
        frame_id: str,
        *,
        location: Optional[str] = None,
        at_time: Optional[str] = None,
        known_at: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> tuple[Observation, ...]:
        when = _parse_time(at_time)
        known = _parse_time(known_at)
        values = self.retrieve(frame_id, location=location)
        if when is not None:
            values = tuple(item for item in values
                           if (_parse_time(item.valid_from) or _parse_time(item.observed_at)) is not None
                           and (_parse_time(item.valid_from) or _parse_time(item.observed_at)) <= when
                           and (_parse_time(item.valid_to) is None or when < _parse_time(item.valid_to)))
        if known is not None:
            # Without recorded_at the system cannot certify when the item was known.
            values = tuple(item for item in values
                           if item.recorded_at is not None and _parse_time(item.recorded_at) <= known)
        if limit is not None:
            if limit < 0:
                raise MemoryConflict("negative memory limit")
            values = values[:limit]
        return tuple(values)

    def current(
        self, frame_id: str, *, location: Optional[str] = None,
        at_time: Optional[str] = None, known_at: Optional[str] = None
    ) -> tuple[Observation, ...]:
        when = _parse_time(at_time) if at_time is not None else datetime.now(timezone.utc)
        candidates = self.historical(frame_id, location=location,
                                     at_time=when.isoformat() if at_time is not None else None,
                                     known_at=known_at)
        if at_time is None:
            candidates = tuple(item for item in candidates
                if (_parse_time(item.valid_from) or _parse_time(item.observed_at)) is None
                or ((_parse_time(item.valid_from) or _parse_time(item.observed_at)) <= when
                and (_parse_time(item.valid_to) is None or when < _parse_time(item.valid_to))))
        result: list[Observation] = []
        for item in candidates:
            replacement_id = self._superseded_by.get(item.object_id) or item.superseded_by
            if replacement_id is not None:
                recorded = self._supersession_recorded.get(item.object_id)
                known = _parse_time(known_at)
                if known is not None and (recorded is None or _parse_time(recorded) > known):
                    # A replacement unknown at this cutoff cannot affect that view.
                    result.append(item)
                    continue
                replacement = self._objects.get(replacement_id)
                effective = self._supersession_effective.get(item.object_id)
                if effective is None and replacement is not None:
                    effective = replacement.valid_from or replacement.observed_at
                if at_time is None:
                    continue
                if effective is not None and _parse_time(effective) <= when:
                    continue
            result.append(item)
        # A later sequence number is not proof that contradictory evidence is resolved.
        return tuple(result)

    def recall(
        self, query: "RecallQuery", *, current_context: str = "", hypotheses: tuple[object, ...] = ()
    ) -> "MemoryContext":
        from ccm.recall.core import recall
        return recall(self, query, current_context=current_context, hypotheses=hypotheses)

    def all(self) -> tuple[Observation, ...]:
        return tuple(self._objects.values())

    def operations(self) -> tuple[MemoryOperation, ...]:
        return tuple(self._operations)

    def supersession_map(self) -> dict[str, str]:
        return dict(self._superseded_by)

    def trace(self) -> list[dict[str, object]]:
        return [
            {"operation": item.operation, "object_id": item.object_id, "sequence": item.sequence}
            for item in self._operations
        ]
