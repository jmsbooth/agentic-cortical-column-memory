"""Structured consensus and explicit non-consensus outcomes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from ccm.schemas.models import Hypothesis, Vote


@dataclass(frozen=True)
class ConsensusResult:
    status: str
    winning_hypothesis: Optional[Hypothesis]
    confidence: float
    support_count: int
    groups: tuple[dict[str, object], ...]
    reason: str

    @property
    def answer(self) -> Optional[str]:
        return self.winning_hypothesis.claim if self.winning_hypothesis else None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "winning_hypothesis": self.winning_hypothesis.to_dict()
            if self.winning_hypothesis
            else None,
            "confidence": self.confidence,
            "support_count": self.support_count,
            "groups": list(self.groups),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReconciliationResult:
    """Compatibility analysis over partial states before any vote is applied."""

    status: str
    compatible_groups: tuple[tuple[str, ...], ...]
    complementary_ids: tuple[str, ...]
    contradictory_ids: tuple[str, ...]
    unresolved_ids: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "compatible_groups": [list(group) for group in self.compatible_groups],
            "complementary_ids": list(self.complementary_ids),
            "contradictory_ids": list(self.contradictory_ids),
            "unresolved_ids": list(self.unresolved_ids),
            "reason": self.reason,
        }


def _key(hypothesis: Hypothesis) -> tuple[str, str, str]:
    return (hypothesis.frame_id, hypothesis.location, hypothesis.claim.strip().casefold())


def compatible(left: Hypothesis, right: Hypothesis) -> bool:
    """Compatibility requires same frame, state, and normalized claim."""

    return _key(left) == _key(right)


def reconcile_hypotheses(hypotheses: Iterable[Hypothesis]) -> ReconciliationResult:
    """Classify local model outputs without forcing a winner.

    Same-frame/location hypotheses with different claims are contradictory;
    hypotheses in different frame locations are complementary.  Structured
    quorum voting remains an optional downstream decision procedure.
    """

    hypotheses = tuple(hypotheses)
    if not hypotheses:
        return ReconciliationResult("unknown", (), (), (), (), "no derived state")
    groups: dict[tuple[str, str, str], list[Hypothesis]] = defaultdict(list)
    by_frame_location: dict[tuple[str, str], list[Hypothesis]] = defaultdict(list)
    for hypothesis in hypotheses:
        groups[_key(hypothesis)].append(hypothesis)
        by_frame_location[(hypothesis.frame_id, hypothesis.location)].append(hypothesis)
    compatible_groups = tuple(
        tuple(item.hypothesis_id for item in values)
        for values in groups.values()
        if len(values) > 1
    )
    contradictory = tuple(
        item.hypothesis_id
        for values in by_frame_location.values()
        if len({item.claim.strip().casefold() for item in values}) > 1
        for item in values
    )
    complementary = tuple(
        item.hypothesis_id
        for key, values in by_frame_location.items()
        if len(values) == 1 and len(by_frame_location) > 1
        for item in values
    )
    unresolved = tuple(dict.fromkeys(contradictory))
    if unresolved:
        status = "contradiction"
        reason = "same frame/location contains incompatible claims"
    elif len(groups) == 1:
        status = "agreement"
        reason = "all local models describe compatible state"
    elif complementary:
        status = "complementary"
        reason = "local models contribute non-overlapping state"
    else:
        status = "unresolved"
        reason = "local model states require additional reconciliation"
    return ReconciliationResult(
        status,
        compatible_groups,
        complementary,
        tuple(dict.fromkeys(contradictory)),
        unresolved,
        reason,
    )


def structured_consensus(
    votes: Iterable[Vote],
    *,
    min_quorum: int = 2,
    min_confidence: float = 0.55,
    min_margin: float = 0.10,
) -> ConsensusResult:
    votes = tuple(votes)
    if not votes:
        return ConsensusResult("abstained", None, 0.0, 0, (), "no valid votes")
    groups: dict[tuple[str, str, str], list[Vote]] = defaultdict(list)
    for vote in votes:
        groups[_key(vote.hypothesis)].append(vote)
    ranked = sorted(
        groups.items(),
        key=lambda item: (
            sum(v.confidence for v in item[1]),
            len(item[1]),
            item[0],
        ),
        reverse=True,
    )
    group_summaries = tuple(
        {
            "frame_id": key[0],
            "location": key[1],
            "claim": key[2],
            "support_count": len(items),
            "confidence_sum": round(sum(v.confidence for v in items), 6),
            "vote_ids": [v.vote_id for v in items],
        }
        for key, items in ranked
    )
    best_key, best_votes = ranked[0]
    best_score = sum(v.confidence for v in best_votes)
    second_score = sum(v.confidence for _, items in ranked[1:2] for v in items)
    winner = max(best_votes, key=lambda item: item.confidence).hypothesis
    if len(best_votes) < min_quorum:
        return ConsensusResult(
            "unresolved", None, best_score / len(votes), len(best_votes), group_summaries,
            "no hypothesis reached quorum",
        )
    if best_score / len(best_votes) < min_confidence:
        return ConsensusResult(
            "abstained", None, best_score / len(best_votes), len(best_votes), group_summaries,
            "quorum confidence below threshold",
        )
    if len(ranked) > 1 and best_score - second_score < min_margin:
        return ConsensusResult(
            "unresolved", None, best_score / len(best_votes), len(best_votes), group_summaries,
            "competing hypotheses are too close to resolve",
        )
    return ConsensusResult(
        "committed", winner, best_score / len(best_votes), len(best_votes), group_summaries,
        "structured hypothesis quorum",
    )


def majority_vote(votes: Iterable[Vote]) -> ConsensusResult:
    """Conventional answer-level majority used as a registered baseline."""

    votes = tuple(votes)
    if not votes:
        return ConsensusResult("abstained", None, 0.0, 0, (), "no votes")
    counts: dict[str, list[Vote]] = defaultdict(list)
    for vote in votes:
        counts[vote.hypothesis.claim.casefold()].append(vote)
    ranked = sorted(counts.items(), key=lambda item: (len(item[1]), item[0]), reverse=True)
    best_key, best_votes = ranked[0]
    if len(ranked) > 1 and len(best_votes) == len(ranked[1][1]):
        return ConsensusResult("unresolved", None, 0.0, len(best_votes), (), "answer-level tie")
    winner = max(best_votes, key=lambda item: item.confidence).hypothesis
    return ConsensusResult(
        "committed", winner, len(best_votes) / len(votes), len(best_votes), (), "answer-level majority"
    )


def confidence_weighted_vote(votes: Iterable[Vote]) -> ConsensusResult:
    """Confidence-weighted answer aggregation without frame compatibility."""

    votes = tuple(votes)
    if not votes:
        return ConsensusResult("abstained", None, 0.0, 0, (), "no votes")
    groups: dict[str, list[Vote]] = defaultdict(list)
    for vote in votes:
        groups[vote.hypothesis.claim.casefold()].append(vote)
    ranked = sorted(
        groups.items(),
        key=lambda item: (sum(v.confidence for v in item[1]), item[0]),
        reverse=True,
    )
    best_key, best_votes = ranked[0]
    best_score = sum(v.confidence for v in best_votes)
    second_score = sum(v.confidence for _, items in ranked[1:2] for v in items)
    if len(ranked) > 1 and abs(best_score - second_score) < 0.10:
        return ConsensusResult("unresolved", None, best_score / len(votes), len(best_votes), (), "weighted tie")
    winner = max(best_votes, key=lambda item: item.confidence).hypothesis
    return ConsensusResult(
        "committed", winner, best_score / sum(v.confidence for v in votes), len(best_votes), (),
        "answer-level confidence weighting",
    )
