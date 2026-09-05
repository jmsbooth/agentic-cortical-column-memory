"""Primary CCM control loop over a model adapter and deterministic environment."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Iterable

from ccm.active_evidence.policy import ActiveEvidencePolicy
from ccm.column.core import Column
from ccm.consensus.voting import ConsensusResult, reconcile_hypotheses, structured_consensus
from ccm.memory.store import MemoryStore
from ccm.recall.core import RecallQuery, assemble_context
from ccm.schemas.models import EvidenceAction, Hypothesis, Observation, ReferenceFrame


ModelProposal = Callable[[str, str, tuple[Observation, ...], tuple[Hypothesis, ...], int], Hypothesis]


class CCMEngine:
    """Runs initialize -> observe -> hypothesize -> exchange -> act -> commit."""

    def __init__(
        self,
        *,
        frame: ReferenceFrame,
        columns: list[Column],
        propose: ModelProposal,
        min_quorum: int = 2,
        allow_active: bool = True,
        use_memory: bool = True,
        use_temporal: bool = True,
        use_reference_frames: bool = True,
        use_structured_vote: bool = True,
        specialize: bool = True,
        max_steps: int = 4,
    ) -> None:
        self.frame = frame
        self.columns = columns
        self.propose = propose
        self.min_quorum = min_quorum
        self.allow_active = allow_active
        self.use_memory = use_memory
        self.use_temporal = use_temporal
        self.use_reference_frames = use_reference_frames
        self.use_structured_vote = use_structured_vote
        self.specialize = specialize
        self.max_steps = max_steps
        self.policy = ActiveEvidencePolicy()

    def solve(
        self,
        *,
        task_id: str,
        initial_observations: Iterable[Observation],
        hypotheses: Iterable[Hypothesis],
        actions: Iterable[EvidenceAction],
        observe_action: Callable[[EvidenceAction], Observation],
        recall_query: str | None = None,
    ) -> dict[str, Any]:
        memory = MemoryStore()
        actions = tuple(actions)
        base_hypotheses = tuple(hypotheses)
        for observation in initial_observations:
            memory.write(observation)
        all_hypotheses = base_hypotheses
        used_actions: set[str] = set()
        action_trace: list[dict[str, Any]] = []
        recall_trace: list[dict[str, Any]] = []
        consensus: ConsensusResult | None = None
        reconciliation = reconcile_hypotheses(())
        step = 0

        while step < self.max_steps:
            if self.use_memory and self.use_temporal:
                memory_context = memory.recall(
                    RecallQuery(
                        query=recall_query or task_id,
                        frame_id=self.frame.frame_id,
                        max_items=64,
                        max_context_tokens=512,
                    ),
                    hypotheses=all_hypotheses,
                )
                observations = memory_context.observations
                recall_trace.append(
                    {
                        "context": memory_context.to_dict(),
                        "assembled_context": assemble_context(memory_context, 512),
                    }
                )
            elif self.use_memory:
                observations = memory.retrieve(self.frame.frame_id)
            else:
                observations = ()
            votes = []
            next_hypotheses = []
            for index, column in enumerate(self.columns):
                for observation in observations:
                    column.observe(observation)
                column_hypotheses = tuple(
                    self.propose(
                        task_id,
                        column.specialization if self.specialize else "shared",
                        observations,
                        all_hypotheses,
                        index,
                    )
                    for _ in [0]
                )
                column.update_hypotheses(column_hypotheses)
                vote = column.vote()
                if vote is not None:
                    next_hypotheses.append(vote.hypothesis)
                    if not self.use_reference_frames:
                        # The ablation keeps answer content but removes frame
                        # and location constraints from the vote key.
                        flattened = replace(vote.hypothesis, frame_id="implicit", location="global")
                        vote = replace(vote, hypothesis=flattened)
                    votes.append(vote)
            for column in self.columns:
                state = column.emit_state()
                for peer in self.columns:
                    if peer.column_id != column.column_id:
                        peer.receive_peer_state(state)

            reconciliation = reconcile_hypotheses(tuple(vote.hypothesis for vote in votes))

            consensus = (
                structured_consensus(votes, min_quorum=self.min_quorum)
                if self.use_structured_vote
                else ConsensusResult(
                    "committed",
                    max(votes, key=lambda item: item.confidence).hypothesis,
                    max(votes, key=lambda item: item.confidence).confidence,
                    1,
                    (),
                    "single-column commit without consensus",
                ) if votes else ConsensusResult("abstained", None, 0.0, 0, (), "no votes")
            )
            # Keep model hypotheses in their owning frame for the next update;
            # a no-reference-frame ablation may flatten only the emitted vote.
            all_hypotheses = tuple(next_hypotheses)
            evidence_present = any(vote.hypothesis.evidence_ids for vote in votes)
            should_seek = (
                self.allow_active
                and not evidence_present
                and bool(actions)
                and consensus.status in {"committed", "unresolved", "abstained"}
            )
            if should_seek:
                action = self.policy.select(
                    all_hypotheses,
                    actions,
                    used_action_ids=used_actions,
                    budget_remaining=float(self.max_steps - step),
                )
                if action is not None:
                    used_actions.add(action.action_id)
                    observation = observe_action(action)
                    memory.write(observation)
                    action_trace.append(
                        {
                            "action_id": action.action_id,
                            "observation_id": observation.object_id,
                            "expected_information_gain": action.expected_information_gain,
                            "accepted": True,
                        }
                    )
                    step += 1
                    continue
            break

        if consensus is None:
            consensus = ConsensusResult("abstained", None, 0.0, 0, (), "no iteration")
        for column in self.columns:
            column.commit(consensus.status)
        return {
            "task_id": task_id,
            "status": consensus.status,
            "answer": consensus.answer,
            "confidence": consensus.confidence,
            "steps": step + 1,
            "consensus": consensus.to_dict(),
            "reconciliation": reconciliation.to_dict(),
            "actions": action_trace,
            "recall": recall_trace,
            "memory": memory.trace(),
            "memory_object_ids": [item.object_id for item in memory.all()],
            "column_states": [column.emit_state().to_dict() for column in self.columns],
            "votes": [vote.to_dict() for vote in votes],
            "use_reference_frames": self.use_reference_frames,
            "use_structured_vote": self.use_structured_vote,
            "use_memory": self.use_memory,
            "use_temporal": self.use_temporal,
        }
