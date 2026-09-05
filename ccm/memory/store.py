"""Append-only structured memory for CCM."""

from __future__ import annotations

from dataclasses import dataclass
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


class MemoryStore:
    """Stores immutable observations and records retrieval/write provenance."""

    def __init__(self) -> None:
        self._objects: dict[str, Observation] = {}
        self._operations: list[MemoryOperation] = []
        self._superseded_by: dict[str, str] = {}

    def write(self, observation: Observation) -> None:
        if observation.object_id in self._objects:
            raise MemoryConflict(f"memory object already exists: {observation.object_id}")
        self._objects[observation.object_id] = observation
        self._operations.append(MemoryOperation("write", observation.object_id, observation.sequence))

    def supersede(self, observation_id: str, replacement_id: str) -> None:
        """Record a current-state replacement without rewriting history."""

        if observation_id not in self._objects or replacement_id not in self._objects:
            raise MemoryConflict("supersession requires two stored observations")
        if observation_id == replacement_id:
            raise MemoryConflict("an observation cannot supersede itself")
        if observation_id in self._superseded_by:
            raise MemoryConflict(f"observation already superseded: {observation_id}")
        self._superseded_by[observation_id] = replacement_id
        self._operations.append(
            MemoryOperation("supersede", observation_id, self._objects[replacement_id].sequence)
        )

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
        limit: Optional[int] = None,
    ) -> tuple[Observation, ...]:
        """Return observations valid at a historical time without collapsing events."""

        values = list(self.retrieve(frame_id, location=location))
        if at_time is not None:
            values = [
                item for item in values
                if (item.valid_from is None or item.valid_from <= at_time)
                and (item.valid_to is None or at_time < item.valid_to)
            ]
        if limit is not None:
            values = values[:limit]
        return tuple(values)

    def current(
        self, frame_id: str, *, location: Optional[str] = None, at_time: Optional[str] = None
    ) -> tuple[Observation, ...]:
        """Return the best current interpretation while retaining all history in ``all``."""

        candidates = [
            item for item in self.historical(frame_id, location=location, at_time=at_time)
            if item.object_id not in self._superseded_by and item.superseded_by is None
        ]
        latest: dict[str, Observation] = {}
        for item in candidates:
            key = item.location
            if key not in latest or (item.sequence, item.object_id) > (latest[key].sequence, latest[key].object_id):
                latest[key] = item
        return tuple(sorted(latest.values(), key=lambda item: (item.sequence, item.object_id)))

    def recall(
        self,
        query: "RecallQuery",
        *,
        current_context: str = "",
        hypotheses: tuple[object, ...] = (),
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
