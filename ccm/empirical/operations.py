"""Deterministic memory input plans at the audited empirical boundary.

These are *instructions* for the future durable-memory adapter, not a second
CCM memory store. Plans must be derivable solely from model-visible data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from ccm.empirical.contracts import BoundaryViolation, ModelVisibleCase


@dataclass(frozen=True)
class MemoryWriteInstruction:
    observation_id: str
    content: str
    source_id: str
    frame_id: str
    location: str
    observed_at: str | None


@dataclass(frozen=True)
class MemoryRecallInstruction:
    case_id: str
    query: str
    max_context_tokens: int
    permitted_source_ids: tuple[str, ...]


def plan_memory_writes(case: ModelVisibleCase) -> tuple[MemoryWriteInstruction, ...]:
    if type(case) is not ModelVisibleCase:
        raise BoundaryViolation("memory ingress requires a model-visible case")
    return tuple(MemoryWriteInstruction(**asdict(obs)) for obs in case.history)


def plan_memory_recall(case: ModelVisibleCase) -> MemoryRecallInstruction:
    if type(case) is not ModelVisibleCase:
        raise BoundaryViolation("memory recall requires a model-visible case")
    return MemoryRecallInstruction(case.case_id, case.question, case.max_context_tokens, case.allowed_source_ids)
