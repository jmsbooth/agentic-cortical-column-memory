import json
import unittest

from ccm.adapters import LLMAdapter
from ccm.schemas.models import Hypothesis, Observation


class AdapterTests(unittest.TestCase):
    def test_provider_neutral_adapter_requires_candidate_and_preserves_evidence(self):
        observation = Observation("obs:1", "ticket says amber", "frame:test", "origin", "ticket:test", 0, 1.0, "run:test")
        candidate = Hypothesis("h:amber", "amber", "frame:test", "origin", (), "task:test", 0.5, 0.5)
        adapter = LLMAdapter(
            lambda payload: json.dumps({"claim": "amber", "confidence": 0.9, "evidence_ids": ["obs:1"]}),
            "provider:test-v1",
        )
        result = adapter.propose("task:test", "retrieval", (observation,), (candidate,), 0)
        self.assertEqual(result.evidence_ids, ("obs:1",))
        self.assertEqual(result.provenance, "model:provider:test-v1:retrieval")
