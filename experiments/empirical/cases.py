"""Unscored preflight examples. Not confirmatory benchmark cases.

Scenario observations encode real facts, not artificial ``supports=<answer>``
labels. The evaluator-only case is constructed separately and never sent to
an adapter or written to memory. No real-model effectiveness is measured here.
"""
from __future__ import annotations

import hashlib
import random

from ccm.empirical.contracts import ModelVisibleCase, VisibleObservation
from evaluation.empirical.oracles import EvaluatorOnlyCase


def make_boundary_fixture(seed: int, ordinal: int) -> tuple[ModelVisibleCase, EvaluatorOnlyCase]:
    case_id = "case:" + hashlib.sha256(f"CCM-EMP-002-fixture:{seed}:{ordinal}".encode()).hexdigest()[:16]
    incumbent, successor = "Maya", "Taylor"
    choices = [incumbent, successor]
    # Randomness is from the case identity only, never a gold/answer flag.
    random.Random(int(hashlib.sha256((case_id + ":options").encode()).hexdigest(), 16)).shuffle(choices)
    history = (
        VisibleObservation(
            observation_id=f"{case_id}:obs:001", content="On February 1 the equipment was assigned to Maya.",
            source_id=f"{case_id}:src:ticket01", frame_id="equipment-ownership", location="device-17",
            observed_at="2026-02-01T09:00:00Z"),
        VisibleObservation(
            observation_id=f"{case_id}:obs:002", content="On February 3 the equipment was reassigned to Taylor.",
            source_id=f"{case_id}:src:ticket02", frame_id="equipment-ownership", location="device-17",
            observed_at="2026-02-03T09:00:00Z"),
    )
    visible = ModelVisibleCase(
        case_id=case_id,
        question="Who was assigned device 17 at the end of February 3? Cite the record used.",
        history=history,
        available_actions=(),
        choices=tuple(choices),
        allowed_source_ids=tuple(obs.source_id for obs in history),
        max_context_tokens=256,
    )
    evaluator = EvaluatorOnlyCase(
        case_id=case_id,
        gold_answer=successor,
        accepted_answers=(successor,),
        valid_evidence_paths=((history[1].observation_id,),),
        hidden_task_family="temporal_supersession_fixture",
    )
    return visible, evaluator
