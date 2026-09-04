"""Append-only structured memory for CCM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ccm.schemas.models import Observation


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

    def write(self, observation: Observation) -> None:
        if observation.object_id in self._objects:
            raise MemoryConflict(f"memory object already exists: {observation.object_id}")
        self._objects[observation.object_id] = observation
        self._operations.append(MemoryOperation("write", observation.object_id, observation.sequence))

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

    def all(self) -> tuple[Observation, ...]:
        return tuple(self._objects.values())

    def operations(self) -> tuple[MemoryOperation, ...]:
        return tuple(self._operations)

    def trace(self) -> list[dict[str, object]]:
        return [
            {"operation": item.operation, "object_id": item.object_id, "sequence": item.sequence}
            for item in self._operations
        ]
