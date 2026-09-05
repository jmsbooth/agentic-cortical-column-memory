import unittest

from ccm.memory.store import MemoryStore
from ccm.recall import RecallQuery, assemble_context
from ccm.schemas.models import Observation


class RecallTests(unittest.TestCase):
    def _observation(self, object_id, content, sequence, relation=""):
        return Observation(
            object_id, content, "frame:incident", "origin", "ticket:test", sequence, 1.0,
            "run:test", relations=(relation,) if relation else (),
        )

    def test_recall_prefers_relevant_evidence_and_returns_provenance(self):
        store = MemoryStore()
        store.write(self._observation("obs:relevant", "credential C7 accessed resource R4", 0, "supports=amber"))
        store.write(self._observation("obs:distractor", "credential C8 accessed resource R9", 1))
        context = store.recall(RecallQuery("C7 resource R4", frame_id="frame:incident", max_items=1))
        self.assertEqual([item.object_id for item in context.observations], ["obs:relevant"])
        self.assertEqual(context.provenance, ("run:test",))
        self.assertIn("provenance=run:test", assemble_context(context, 64))

    def test_recall_is_bounded_and_keeps_conflicts_visible(self):
        store = MemoryStore()
        store.write(self._observation("obs:a", "status is open", 0))
        store.write(self._observation("obs:b", "status is closed", 1))
        context = store.recall(RecallQuery("status", frame_id="frame:incident", max_items=8, max_context_tokens=12))
        self.assertEqual(context.unresolved_conflicts, (("obs:a", "obs:b"),))
        self.assertLessEqual(context.context_tokens, 20)
