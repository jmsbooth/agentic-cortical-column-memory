"""Empirical model adapter: typed model-visible input only.

This is deliberately separate from the legacy hypothesis/candidate API used in
software smoke tests. It does not import an evaluator, label store or scorer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from ccm.empirical.contracts import BoundaryViolation, ModelVisibleCase


@dataclass(frozen=True)
class EmpiricalAnswer:
    answer: str
    evidence_ids: tuple[str, ...]
    abstained: bool


class EmpiricalLLMAdapter:
    def __init__(self, complete: Callable[[str], str], *, version: str, backend: str):
        if not callable(complete) or not version or not backend:
            raise ValueError("empirical adapter requires a client, version and backend")
        if any(text in f"{version} {backend}".lower() for text in ("toy", "symbolic", "oracle", "smoke")):
            raise BoundaryViolation("symbolic/toy backend is not an empirical LLM")
        self._complete = complete
        self.version = version
        self.backend = backend

    def answer_case(self, case: ModelVisibleCase) -> EmpiricalAnswer:
        if type(case) is not ModelVisibleCase:
            raise BoundaryViolation("empirical adapter accepts only ModelVisibleCase")
        # The model receives only the audited, explicit visible data contract.
        payload = case.to_json()
        result = json.loads(self._complete(payload))
        if not isinstance(result, dict) or set(result) != {"answer", "evidence_ids", "abstained"}:
            raise BoundaryViolation("model reply must have exact answer/evidence/abstained schema")
        if not isinstance(result["answer"], str) or type(result["abstained"]) is not bool:
            raise BoundaryViolation("invalid model answer type")
        if not isinstance(result["evidence_ids"], list) or not all(isinstance(i, str) for i in result["evidence_ids"]):
            raise BoundaryViolation("evidence_ids must be strings")
        visible_ids = {item.observation_id for item in case.history}
        if not set(result["evidence_ids"]).issubset(visible_ids):
            raise BoundaryViolation("model referenced foreign or fabricated evidence")
        if len(set(result["evidence_ids"])) != len(result["evidence_ids"]):
            raise BoundaryViolation("duplicate evidence IDs")
        if result["abstained"] and result["answer"].strip():
            raise BoundaryViolation("abstained responses must not assert an answer")
        return EmpiricalAnswer(
            answer=result["answer"],
            evidence_ids=tuple(result["evidence_ids"]),
            abstained=result["abstained"],
        )
