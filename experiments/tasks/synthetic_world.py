"""Versioned, deterministic task worlds with hidden ground truth.

The worlds are deliberately small and inspectable.  They validate protocol
mechanics; they are not evidence that a language model has solved the task
classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ccm.schemas.models import EvidenceAction, Hypothesis, Observation, ReferenceFrame, Transition

TASK_VERSION = "synthetic-world-v0.1.0"
TASK_CLASSES = (
    "persistent_memory",
    "multi_hop_evidence",
    "active_information",
    "ambiguous_hypothesis",
    "tool_use",
    "long_horizon",
    "conflicting_evidence",
    "incomplete_information",
    "pure_reasoning",
)


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
) -> Observation:
    return Observation(
        object_id=f"{task_id}:obs:{suffix}",
        content=content,
        frame_id=frame_id,
        location=location,
        source="environment:synthetic-v0.1.0",
        sequence=sequence,
        confidence=1.0,
        provenance=f"synthetic-world:{task_id}",
        validation_state="validated",
        relations=tuple(relations),
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
    if task_class not in TASK_CLASSES:
        raise ValueError(f"unknown task class: {task_class}")
    task_id = f"{task_class}:{seed}:{ordinal:03d}"
    frame = _frame(task_id, "conceptual-workspace" if task_class != "tool_use" else "tool-state")
    answer = "amber" if (seed + ordinal) % 2 == 0 else "indigo"
    alternative = "violet" if answer == "amber" else "ochre"
    initial: tuple[Observation, ...] = ()
    actions: tuple[EvidenceAction, ...] = ()
    required: tuple[str, ...] = ()
    prompt = f"Resolve the hidden state for {task_class.replace('_', ' ')} task {ordinal}."

    if task_class == "persistent_memory":
        initial = (
            _observation(task_id, "archive", "An archived record identifies the keyed value.", frame.frame_id, "origin", 0, f"supports={answer}"),
        )
        required = (initial[0].object_id,)
    elif task_class == "multi_hop_evidence":
        initial = (
            _observation(task_id, "fact-a", "The first relation points to an intermediate state.", frame.frame_id, "origin", 0, "supports=intermediate"),
            _observation(task_id, "fact-b", "The second relation maps the intermediate state to the answer.", frame.frame_id, "inspection", 1, f"supports={answer}"),
        )
        required = tuple(item.object_id for item in initial)
    elif task_class == "active_information":
        actions = (_action(task_id, "measure", frame, "Measure the unresolved attribute.", 0, 1.0, f"supports={answer}"),)
        required = (actions[0].observation.object_id,)
    elif task_class == "ambiguous_hypothesis":
        actions = (
            _action(task_id, "cheap", frame, "Inspect a weakly discriminative cue.", 0, 0.2, f"supports={alternative}"),
            _action(task_id, "decisive", frame, "Acquire the observation that separates the hypotheses.", 1, 1.0, f"supports={answer}"),
        )
        required = (actions[1].observation.object_id,)
    elif task_class == "tool_use":
        actions = (_action(task_id, "tool", frame, "Query the deterministic state tool.", 0, 1.0, f"supports={answer}"),)
        required = (actions[0].observation.object_id,)
    elif task_class == "long_horizon":
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
