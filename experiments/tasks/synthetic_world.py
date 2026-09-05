"""Versioned, deterministic task worlds with hidden ground truth.

The worlds are deliberately small and inspectable.  They validate protocol
mechanics; they are not evidence that a language model has solved the task
classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ccm.schemas.models import EvidenceAction, Hypothesis, Observation, ReferenceFrame, Transition

TASK_VERSION = "synthetic-memory-world-v0.1.0"
TASK_CLASSES = (
    "persistent_factual_recall",
    "temporal_state",
    "relational_recall",
    "conflicting_evidence",
    "state_supersession",
    "provenance_recall",
    "cross_frame_integration",
    "distractor_resistance",
    "long_horizon_continuity",
    "active_evidence",
    "incomplete_information",
    "pure_reasoning",
)

LEGACY_TASK_CLASS_ALIASES = {
    "persistent_memory": "persistent_factual_recall",
    "multi_hop_evidence": "relational_recall",
    "active_information": "active_evidence",
    "ambiguous_hypothesis": "active_evidence",
    "long_horizon": "long_horizon_continuity",
    "tool_use": "active_evidence",
}


@dataclass(frozen=True)
class SyntheticTask:
    task_id: str
    task_class: str
    prompt: str
    frame: ReferenceFrame
    answer: str
    candidate_answers: tuple[str, ...]
    initial_observations: tuple[Observation, ...]
    actions: tuple[EvidenceAction, ...]
    required_observation_ids: tuple[str, ...]
    max_steps: int = 4

    def hypotheses(self) -> tuple[Hypothesis, ...]:
        return tuple(
            Hypothesis(
                hypothesis_id=f"{self.task_id}:h{index}",
                claim=claim,
                frame_id=self.frame.frame_id,
                location=self.frame.origin,
                evidence_ids=(),
                provenance="task:candidate-set",
                confidence=0.5,
                uncertainty=0.5,
            )
            for index, claim in enumerate(self.candidate_answers)
        )


def _frame(task_id: str, kind: str) -> ReferenceFrame:
    return ReferenceFrame(
        frame_id=f"frame:{task_id}",
        kind=kind,
        origin="origin",
        state="origin",
        transitions=(
            Transition("inspect", "origin", "inspection"),
            Transition("verify", "inspection", "verified"),
        ),
    )


def _observation(
    task_id: str,
    suffix: str,
    content: str,
    frame_id: str,
    location: str,
    sequence: int,
    *relations: str,
    observed_at: str | None = None,
    recorded_at: str | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
    superseded_by: str | None = None,
    source: str = "environment:synthetic-v0.1.0",
) -> Observation:
    return Observation(
        object_id=f"{task_id}:obs:{suffix}",
        content=content,
        frame_id=frame_id,
        location=location,
        source=source,
        sequence=sequence,
        confidence=1.0,
        provenance=f"synthetic-world:{task_id}",
        validation_state="validated",
        relations=tuple(relations),
        observed_at=observed_at,
        recorded_at=recorded_at,
        valid_from=valid_from,
        valid_to=valid_to,
        superseded_by=superseded_by,
    )


def _action(
    task_id: str,
    suffix: str,
    frame: ReferenceFrame,
    content: str,
    sequence: int,
    gain: float,
    *relations: str,
) -> EvidenceAction:
    observation = _observation(
        task_id,
        f"action-{suffix}",
        content,
        frame.frame_id,
        "inspection",
        sequence,
        *relations,
    )
    return EvidenceAction(
        action_id=f"{task_id}:action:{suffix}",
        description=content,
        target_hypothesis_ids=(f"{task_id}:h0", f"{task_id}:h1"),
        observation=observation,
        expected_information_gain=gain,
        cost=1.0,
        tool_name="synthetic_observer",
    )


def make_task(task_class: str, ordinal: int, seed: int) -> SyntheticTask:
    task_class = LEGACY_TASK_CLASS_ALIASES.get(task_class, task_class)
    if task_class not in TASK_CLASSES:
        raise ValueError(f"unknown task class: {task_class}")
    task_id = f"{task_class}:{seed}:{ordinal:03d}"
    frame = _frame(task_id, "conceptual-workspace")
    answer = "amber" if (seed + ordinal) % 2 == 0 else "indigo"
    alternative = "violet" if answer == "amber" else "ochre"
    initial: tuple[Observation, ...] = ()
    actions: tuple[EvidenceAction, ...] = ()
    required: tuple[str, ...] = ()
    prompt = f"Resolve the hidden state for {task_class.replace('_', ' ')} task {ordinal}."

    if task_class == "persistent_factual_recall":
        initial = (
            _observation(task_id, "archive", "An archived record identifies the keyed value.", frame.frame_id, "origin", 0, f"supports={answer}"),
        )
        required = (initial[0].object_id,)
    elif task_class == "temporal_state":
        initial = (
            _observation(
                task_id, "historical", "The device was assigned to the former owner.",
                frame.frame_id, "origin", 0, f"supports={alternative}",
                observed_at="2026-01-01T09:00:00Z", valid_from="2026-01-01T09:00:00Z",
                valid_to="2026-02-01T09:00:00Z",
            ),
            _observation(
                task_id, "current", "The device is assigned to the current owner.",
                frame.frame_id, "origin", 1, f"supports={answer}",
                observed_at="2026-02-01T09:00:00Z", valid_from="2026-02-01T09:00:00Z",
            ),
        )
        required = (initial[1].object_id,)
    elif task_class == "relational_recall":
        initial = (
            _observation(task_id, "fact-a", "The first relation points to an intermediate state.", frame.frame_id, "origin", 0, "supports=intermediate"),
            _observation(task_id, "fact-b", "The second relation maps the intermediate state to the answer.", frame.frame_id, "inspection", 1, f"supports={answer}"),
        )
        required = tuple(item.object_id for item in initial)
    elif task_class == "state_supersession":
        old_id = f"{task_id}:obs:old-state"
        current_id = f"{task_id}:obs:current-state"
        initial = (
            _observation(task_id, "old-state", "The resource had the previous status.", frame.frame_id, "origin", 0, f"supports={alternative}", superseded_by=current_id),
            _observation(task_id, "current-state", "The resource has the replacement status.", frame.frame_id, "origin", 1, f"supports={answer}", observed_at="2026-03-01T09:00:00Z"),
        )
        required = (current_id,)
    elif task_class == "provenance_recall":
        initial = (
            _observation(task_id, "ticket", "The incident ticket records the keyed value.", frame.frame_id, "origin", 0, f"supports={answer}", source="incident-ticket:INC-19"),
        )
        required = (initial[0].object_id,)
    elif task_class == "cross_frame_integration":
        initial = (
            _observation(task_id, "actor", "The actor relation identifies the intermediate state.", frame.frame_id, "origin", 0, "supports=intermediate", "frame=actor"),
            _observation(task_id, "resource", "The resource relation resolves the answer.", frame.frame_id, "inspection", 1, f"supports={answer}", "frame=resource"),
        )
        required = tuple(item.object_id for item in initial)
    elif task_class == "distractor_resistance":
        initial = (
            _observation(task_id, "signal", "The relevant record identifies the keyed value.", frame.frame_id, "origin", 0, f"supports={answer}"),
            _observation(task_id, "distractor-a", "An unrelated record shares vocabulary but is not relevant.", frame.frame_id, "origin", 1),
            _observation(task_id, "distractor-b", "Another unrelated record should be rejected.", frame.frame_id, "origin", 2),
        )
        required = (initial[0].object_id,)
    elif task_class == "active_evidence":
        actions = (_action(task_id, "measure", frame, "Measure the unresolved attribute.", 0, 1.0, f"supports={answer}"),)
        required = (actions[0].observation.object_id,)
    elif task_class == "long_horizon_continuity":
        actions = (
            _action(task_id, "locate", frame, "Locate the relevant state.", 0, 0.5, "supports=intermediate"),
            _action(task_id, "verify", frame, "Verify the located state.", 1, 1.0, f"supports={answer}"),
        )
        required = (actions[1].observation.object_id,)
    elif task_class == "conflicting_evidence":
        initial = (
            _observation(task_id, "source-a", "Source A reports one value.", frame.frame_id, "origin", 0, f"supports={answer}"),
            _observation(task_id, "source-b", "Source B reports a conflicting value.", frame.frame_id, "origin", 1, f"supports={alternative}"),
        )
    elif task_class == "incomplete_information":
        prompt += " The correct outcome may be insufficient evidence."
    elif task_class == "pure_reasoning":
        prompt += " No external observation is available; use the local prior."

    return SyntheticTask(
        task_id=task_id,
        task_class=task_class,
        prompt=prompt,
        frame=frame,
        answer=answer,
        candidate_answers=(answer, alternative),
        initial_observations=initial,
        actions=actions,
        required_observation_ids=required,
        max_steps=4,
    )


def build_suite(seed: int, task_classes: Iterable[str], tasks_per_class: int) -> tuple[SyntheticTask, ...]:
    if tasks_per_class < 1:
        raise ValueError("tasks_per_class must be positive")
    return tuple(
        make_task(task_class, ordinal, seed)
        for task_class in task_classes
        for ordinal in range(tasks_per_class)
    )
