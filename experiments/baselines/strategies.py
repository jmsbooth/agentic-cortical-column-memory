"""Registered baselines and the dependency-free symbolic model adapter."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

from ccm.column.core import Column
from ccm.consensus.voting import ConsensusResult, confidence_weighted_vote, majority_vote
from ccm.orchestration.engine import CCMEngine
from ccm.schemas.models import Hypothesis, Observation
from evaluation.resource_accounting.accounting import ResourceMeter
from experiments.tasks.synthetic_world import SyntheticTask


STRATEGIES = (
    "M0",
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "CCM-NoRF",
    "CCM-NoModules",
    "CCM-NoTemporal",
    "CCM-NoReconciliation",
    "CCM-NoActive",
    "CCM-FlatLedger",
    # Secondary inference/composition baselines retained for exploratory runs.
    "B0",
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    # v0.1.0 compatibility aliases; the registered matrix uses M0-M6.
    "CCM-Full",
    "CCM-NoVote",
    "CCM-NoStructuredMemory",
    "CCM-NoSpecialization",
)


class ToyModel:
    """Deterministic adapter used for software tests, not a model benchmark."""

    version = "toy-symbolic-v0.1.0"

    def __init__(self, seed: int):
        self.seed = seed

    def _pick_without_evidence(self, task: SyntheticTask, index: int, specialization: str) -> str:
        digest = hashlib.sha256(
            f"{self.seed}:{task.task_id}:{index}:{specialization}".encode("utf-8")
        ).digest()
        # The toy model has a visible, fixed prior; the architecture must not
        # be credited for changing this intrinsic reasoning control.
        return task.answer if digest[0] % 10 < 6 else task.candidate_answers[1]

    def propose(
        self,
        task: SyntheticTask,
        specialization: str,
        observations: tuple[Observation, ...],
        candidates: tuple[Hypothesis, ...],
        index: int,
    ) -> Hypothesis:
        support: dict[str, list[str]] = {}
        for observation in observations:
            for relation in observation.relations:
                if relation.startswith("supports="):
                    support.setdefault(relation.split("=", 1)[1], []).append(observation.object_id)
        candidate_claims = {item.claim for item in candidates}
        supported = sorted(item for item in support if item in candidate_claims)
        if len(supported) == 1:
            claim = supported[0]
        elif len(supported) > 1:
            claim = supported[index % len(supported)]
        else:
            claim = self._pick_without_evidence(task, index, specialization)
        evidence_ids = tuple(support.get(claim, ()))
        if task.task_class == "incomplete_information" and not evidence_ids:
            confidence = 0.42
        elif len(supported) > 1:
            # Contradictory external evidence is deliberately below the
            # commit threshold; the architecture must preserve uncertainty.
            confidence = 0.50
        elif evidence_ids:
            confidence = 0.88
        else:
            confidence = 0.62
        template = next(item for item in candidates if item.claim == claim)
        return replace(
            template,
            evidence_ids=evidence_ids,
            provenance=f"model:{self.version}:{specialization}",
            confidence=confidence,
            uncertainty=round(1.0 - confidence, 6),
        )


def _hypothesis_vote(task: SyntheticTask, model: ToyModel, index: int, use_context: bool) -> Hypothesis:
    observations = task.initial_observations if use_context else ()
    return model.propose(task, f"baseline-{index}", observations, task.hypotheses(), index)


def _record_single(task: SyntheticTask, strategy: str, model: ToyModel, meter: ResourceMeter) -> dict[str, Any]:
    use_context = strategy in {"B1", "B4", "B5"}
    count = 1 if strategy in {"B0", "B1"} else 5 if strategy == "B2" else 3
    votes = []
    for index in range(count):
        meter.model_call(task.prompt, "structured hypothesis")
        hypothesis = _hypothesis_vote(task, model, index, use_context)
        from ccm.schemas.models import Vote

        votes.append(
            Vote(
                vote_id=f"{strategy}:{task.task_id}:{index}",
                column_id=f"{strategy}-column-{index}",
                hypothesis_id=hypothesis.hypothesis_id,
                hypothesis=hypothesis,
                confidence=hypothesis.confidence,
            )
        )
    if strategy == "B3":
        result = ConsensusResult("committed", votes[0].hypothesis, votes[0].confidence, 1, (), "first agent output")
    elif strategy == "B5":
        result = confidence_weighted_vote(votes)
    elif strategy == "B0" or strategy == "B1":
        result = majority_vote(votes)
    elif strategy == "B2" or strategy == "B3":
        result = majority_vote(votes)
    else:
        result = majority_vote(votes)
    if votes:
        for _ in range(max(0, len(votes) - 1)):
            meter.communication(96)
    return {
        "status": result.status,
        "answer": result.answer,
        "confidence": result.confidence,
        "steps": 1,
        "actions": [],
        "votes": [vote.to_dict() for vote in votes],
        "memory": [],
        "column_states": [],
        "consensus": result.to_dict(),
    }


def _record_memory_baseline(
    task: SyntheticTask, strategy: str, model: ToyModel, meter: ResourceMeter
) -> dict[str, Any]:
    """Run a primary conventional memory baseline with matched inputs."""

    use_memory = strategy != "M0"
    observations = task.initial_observations if use_memory else ()
    if strategy == "M2":
        # This smoke adapter uses an inspectable last-observation summary. It
        # is a protocol placeholder, not a claim about learned summarization.
        observations = observations[-1:] if observations else ()
    meter.model_call(task.prompt, f"{strategy} memory baseline")
    hypothesis = model.propose(task, strategy, observations, task.hypotheses(), 0)
    from ccm.schemas.models import Vote

    vote = Vote(
        vote_id=f"{strategy}:{task.task_id}:0",
        column_id=f"{strategy}:memory",
        hypothesis_id=hypothesis.hypothesis_id,
        hypothesis=hypothesis,
        confidence=hypothesis.confidence,
    )
    result = majority_vote((vote,))
    bytes_stored = sum(len(item.content.encode("utf-8")) for item in observations)
    meter.memory_update(objects=len(observations), bytes_stored=bytes_stored)
    if use_memory:
        meter.recall(
            candidates=len(observations),
            context_tokens=sum(len(item.content.split()) for item in observations),
            latency_ms=0.0,
        )
    return {
        "status": result.status,
        "answer": result.answer,
        "confidence": result.confidence,
        "steps": 1,
        "actions": [],
        "votes": [vote.to_dict()],
        "memory": [
            {"operation": "retrieve", "object_id": item.object_id, "sequence": item.sequence}
            for item in observations
        ],
        "memory_object_ids": [item.object_id for item in observations],
        "recall": {"baseline": strategy, "context_tokens": sum(len(item.content.split()) for item in observations)},
        "column_states": [],
        "consensus": result.to_dict(),
        "reconciliation": {"status": "agreement", "reason": "single baseline state"},
    }


def run_strategy(task: SyntheticTask, strategy: str, seed: int) -> tuple[dict[str, Any], ResourceMeter]:
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy}")
    meter = ResourceMeter()
    model = ToyModel(seed)
    if strategy.startswith("B"):
        trace = _record_single(task, strategy, model, meter)
    elif strategy in {"M0", "M1", "M2", "M3", "M4", "M5"}:
        trace = _record_memory_baseline(task, strategy, model, meter)
    else:
        flags = {
            "M6": (True, True, True, True, True, 3),
            "CCM-Full": (True, True, True, True, True, 3),
            "CCM-NoRF": (True, True, True, True, True, 3),
            "CCM-NoModules": (True, True, True, True, True, 1),
            "CCM-NoTemporal": (True, True, True, True, False, 3),
            "CCM-NoReconciliation": (True, True, False, True, True, 3),
            "CCM-NoActive": (False, True, True, True, True, 3),
            "CCM-FlatLedger": (True, True, True, True, True, 3),
            "CCM-NoVote": (True, True, False, True, True, 3),
            "CCM-NoStructuredMemory": (True, False, True, True, True, 3),
            "CCM-NoSpecialization": (True, True, True, False, True, 3),
        }[strategy]
        allow_active, use_memory, use_vote, specialize, use_temporal, column_count = flags
        columns = [
            Column(f"{strategy}:column:{index}", task.frame, f"specialization-{index}")
            for index in range(column_count)
        ]

        def propose(
            _task_id: str,
            specialization: str,
            observations: tuple[Observation, ...],
            candidates: tuple[Hypothesis, ...],
            index: int,
        ) -> Hypothesis:
            meter.model_call(task.prompt, "structured hypothesis")
            return model.propose(task, specialization, observations, candidates, index)

        engine = CCMEngine(
            frame=task.frame,
            columns=columns,
            propose=propose,
            min_quorum=1 if strategy == "CCM-NoModules" else 2,
            allow_active=allow_active,
            use_memory=use_memory,
            use_temporal=use_temporal,
            use_reference_frames=strategy not in {"CCM-NoRF", "CCM-FlatLedger"},
            use_structured_vote=use_vote,
            specialize=specialize,
            max_steps=task.max_steps,
        )

        def observe_action(action: Any) -> Observation:
            meter.action()
            return action.observation

        trace = engine.solve(
            task_id=task.task_id,
            initial_observations=task.initial_observations,
            hypotheses=task.hypotheses(),
            actions=task.actions,
            observe_action=observe_action,
            recall_query=task.prompt,
        )
        meter.communication(256 * len(columns))
        writes = [item for item in trace.get("memory", []) if item.get("operation") == "write"]
        recalls = trace.get("recall", [])
        meter.memory_update(
            objects=len(writes),
            bytes_stored=sum(len(item["object_id"].encode("utf-8")) for item in writes),
        )
        meter.recall(
            candidates=sum(
                len(item.get("context", {}).get("observations", [])) for item in recalls
            ),
            context_tokens=sum(len(item.get("assembled_context", "").split()) for item in recalls),
            latency_ms=0.0,
        )
    return trace, meter
