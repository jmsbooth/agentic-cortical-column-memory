"""Fail-closed, model-visible contracts for CCM-EMP-002.

There are deliberately no gold answers, grader metadata or evaluation
imports in this module. An evaluator has a separate schema and storage path.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping


class BoundaryViolation(ValueError):
    """Reject a payload that violates the empirical model/evaluator boundary."""


CASE_RE = re.compile(r"case:[0-9a-f]{16}\Z")
FORBIDDEN_NAME_RE = re.compile(
    r"(?:ground[_-]?truth|gold[_-]?answer|answer[_-]?key|"
    r"correct[_-]?candidate|expected[_-]?answer|evaluator[_-]?only|"
    r"grader[_-]?label|label[_-]?canary|scoring[_-]?metadata)",
    flags=re.IGNORECASE,
)
FORBIDDEN_CONTENT_RE = re.compile(
    r"(?:\bsupports\s*=|\b(?:ground[_-]?truth|gold[_-]?answer|"
    r"answer[_-]?key|evaluator[_-]?only|grader[_-]?label|"
    r"label[_-]?canary)\s*[:=]|__EVALUATOR_ONLY_)",
    flags=re.IGNORECASE,
)


def _check_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise BoundaryViolation(f"{field_name} must be nonempty text")
    if FORBIDDEN_CONTENT_RE.search(value):
        raise BoundaryViolation(f"{field_name} includes evaluator-only notation")


def _check_fields(data: Mapping[str, Any], permitted: set[str]) -> None:
    if not isinstance(data, dict):
        raise BoundaryViolation("case payload must be a JSON object")
    extra = set(data) - permitted
    missing = permitted - set(data)
    if extra or missing:
        raise BoundaryViolation(f"case schema mismatch: unexpected={sorted(extra)}, missing={sorted(missing)}")
    if any(FORBIDDEN_NAME_RE.search(str(key)) for key in data):
        raise BoundaryViolation("evaluator-only schema key detected")


def _scoped_id(case_id: str, obj_id: str, kind: str) -> None:
    _check_string(obj_id, kind)
    if not obj_id.startswith(f"{case_id}:{kind}:") or len(obj_id) <= len(f"{case_id}:{kind}:"):
        raise BoundaryViolation(f"{kind} id is not scoped to current case")


@dataclass(frozen=True)
class VisibleObservation:
    observation_id: str
    content: str
    source_id: str
    frame_id: str
    location: str
    observed_at: str | None = None

    def verify(self, case_id: str) -> None:
        _scoped_id(case_id, self.observation_id, "obs")
        _scoped_id(case_id, self.source_id, "src")
        for field_name in ("content", "frame_id", "location"):
            _check_string(getattr(self, field_name), field_name)
        if self.observed_at is not None:
            _check_string(self.observed_at, "observed_at")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisibleObservation":
        _check_fields(data, {field.name for field in fields(cls)})
        return cls(**data)


@dataclass(frozen=True)
class VisibleAction:
    action_id: str
    description: str
    tool_name: str

    def verify(self, case_id: str) -> None:
        _scoped_id(case_id, self.action_id, "action")
        _check_string(self.description, "action description")
        _check_string(self.tool_name, "tool name")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisibleAction":
        _check_fields(data, {field.name for field in fields(cls)})
        return cls(**data)


@dataclass(frozen=True)
class ModelVisibleCase:
    """The *only* case object authorized across an empirical model boundary.

    A serialized copy is made by explicit allowlist, not from an evaluator
    dataclass or a generic task's ``__dict__``.
    """

    case_id: str
    question: str
    history: tuple[VisibleObservation, ...]
    available_actions: tuple[VisibleAction, ...]
    choices: tuple[str, ...]
    allowed_source_ids: tuple[str, ...]
    max_context_tokens: int

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or CASE_RE.fullmatch(self.case_id) is None:
            raise BoundaryViolation("invalid opaque case identity")
        _check_string(self.question, "question")
        if type(self.max_context_tokens) is not int or self.max_context_tokens <= 0:
            raise BoundaryViolation("context token budget must be positive")
        if not isinstance(self.history, tuple) or not isinstance(self.available_actions, tuple):
            raise BoundaryViolation("history and actions must be immutable tuples")
        if not isinstance(self.choices, tuple) or not isinstance(self.allowed_source_ids, tuple):
            raise BoundaryViolation("choices and source identities must be immutable tuples")
        seen_obs: set[str] = set()
        for observation in self.history:
            if not isinstance(observation, VisibleObservation):
                raise BoundaryViolation("history contains unapproved observation type")
            observation.verify(self.case_id)
            if observation.observation_id in seen_obs:
                raise BoundaryViolation("duplicate observation identity")
            seen_obs.add(observation.observation_id)
        seen_actions: set[str] = set()
        for action in self.available_actions:
            if not isinstance(action, VisibleAction):
                raise BoundaryViolation("actions contain an unapproved type")
            action.verify(self.case_id)
            if action.action_id in seen_actions:
                raise BoundaryViolation("duplicate action identity")
            seen_actions.add(action.action_id)
        if len(set(self.choices)) != len(self.choices):
            raise BoundaryViolation("duplicate choices")
        for choice in self.choices:
            _check_string(choice, "choice")
        for source_id in self.allowed_source_ids:
            _scoped_id(self.case_id, source_id, "src")
        if set(self.allowed_source_ids) != {obs.source_id for obs in self.history}:
            raise BoundaryViolation("allowed source IDs must match this case's history exactly")
        if len(set(self.allowed_source_ids)) != len(self.allowed_source_ids):
            raise BoundaryViolation("duplicate source IDs")

    def to_dict(self) -> dict[str, Any]:
        # No evaluator object is ever accepted by this function.
        return {
            "case_id": self.case_id,
            "question": self.question,
            "history": [asdict(item) for item in self.history],
            "available_actions": [asdict(item) for item in self.available_actions],
            "choices": list(self.choices),
            "allowed_source_ids": list(self.allowed_source_ids),
            "max_context_tokens": self.max_context_tokens,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelVisibleCase":
        _check_fields(data, {field.name for field in fields(cls)})
        if not all(isinstance(data[key], list) for key in ("history", "available_actions", "choices", "allowed_source_ids")):
            raise BoundaryViolation("model-visible arrays must be JSON arrays")
        return cls(
            case_id=data["case_id"],
            question=data["question"],
            history=tuple(VisibleObservation.from_dict(v) for v in data["history"]),
            available_actions=tuple(VisibleAction.from_dict(v) for v in data["available_actions"]),
            choices=tuple(data["choices"]),
            allowed_source_ids=tuple(data["allowed_source_ids"]),
            max_context_tokens=data["max_context_tokens"],
        )

    @classmethod
    def from_json(cls, payload: str) -> "ModelVisibleCase":
        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise BoundaryViolation(f"duplicate payload key: {key}")
                result[key] = value
            return result
        return cls.from_dict(json.loads(payload, object_pairs_hook=reject_duplicates))
