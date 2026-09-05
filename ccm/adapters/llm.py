"""Provider-neutral interface for plugging an actual reasoning model into CCM."""

from __future__ import annotations

import json
from typing import Callable, Protocol

from ccm.schemas.models import Hypothesis, Observation


class ModelAdapter(Protocol):
    """Minimal interface required by a CCM column owner."""

    version: str

    def propose(
        self,
        task_id: str,
        specialization: str,
        observations: tuple[Observation, ...],
        candidates: tuple[Hypothesis, ...],
        index: int,
    ) -> Hypothesis:
        ...


class LLMAdapter:
    """JSON-boundary adapter for hosted, local, or frontier model clients.

    The client is injected by the caller.  This module performs no network
    access and never promotes arbitrary model text to an observation.
    """

    def __init__(self, complete: Callable[[str], str], version: str):
        if not version or not callable(complete):
            raise ValueError("an LLM adapter requires a callable client and version")
        self.complete = complete
        self.version = version

    def propose(
        self,
        task_id: str,
        specialization: str,
        observations: tuple[Observation, ...],
        candidates: tuple[Hypothesis, ...],
        index: int,
    ) -> Hypothesis:
        if not candidates:
            raise ValueError("an LLM adapter requires candidate hypotheses")
        payload = {
            "task_id": task_id,
            "specialization": specialization,
            "observations": [item.to_dict() for item in observations],
            "candidate_hypotheses": [item.to_dict() for item in candidates],
        }
        response = json.loads(self.complete(json.dumps(payload, sort_keys=True)))
        claim = str(response.get("claim", ""))
        template = next((item for item in candidates if item.claim == claim), None)
        if template is None:
            raise ValueError("LLM response claim must match a supplied candidate")
        confidence = float(response.get("confidence", template.confidence))
        evidence_ids = tuple(
            item.object_id for item in observations
            if item.object_id in set(response.get("evidence_ids", []))
        )
        return Hypothesis(
            hypothesis_id=f"{task_id}:llm:{index}",
            claim=template.claim,
            frame_id=template.frame_id,
            location=template.location,
            evidence_ids=evidence_ids,
            provenance=f"model:{self.version}:{specialization}",
            confidence=confidence,
            uncertainty=round(1.0 - confidence, 6),
            requested_action=response.get("requested_action"),
        )
