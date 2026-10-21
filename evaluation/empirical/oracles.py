"""Evaluator-only answer data. Never import into model-visible adapter code."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluatorOnlyCase:
    case_id: str
    gold_answer: str
    accepted_answers: tuple[str, ...]
    valid_evidence_paths: tuple[tuple[str, ...], ...]
    hidden_task_family: str
    scoring_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        from ccm.empirical.contracts import CASE_RE
        if CASE_RE.fullmatch(self.case_id) is None:
            raise ValueError("invalid evaluator case ID")
        if not self.gold_answer or not self.hidden_task_family:
            raise ValueError("evaluation requires gold and task family")
        if self.gold_answer not in self.accepted_answers:
            raise ValueError("gold must be included in accepted answers")
