import unittest

from ccm.column.core import Column
from ccm.consensus.voting import structured_consensus
from ccm.schemas.models import Hypothesis, ReferenceFrame, Vote


def hypothesis(identifier, claim, confidence, frame="frame:test"):
    return Hypothesis(identifier, claim, frame, "origin", (), "model:test", confidence, 1 - confidence)


class ColumnConsensusTests(unittest.TestCase):
    def _vote(self, column_id, item):
        return Vote(f"vote:{column_id}", column_id, item.hypothesis_id, item, item.confidence)

    def test_column_state_and_peer_ingestion(self):
        frame = ReferenceFrame("frame:test", "conceptual", "origin", "origin")
        left = Column("left", frame, "retrieval")
        right = Column("right", frame, "state")
        item = hypothesis("h:1", "amber", 0.9)
        left.update_hypotheses([item])
        right.receive_peer_state(left.emit_state())
        self.assertEqual(right.emit_state().peer_column_ids, ("left",))
        self.assertEqual(left.vote().hypothesis_id, "h:1")

    def test_agreement_commits(self):
        item = hypothesis("h:1", "amber", 0.8)
        result = structured_consensus([self._vote("a", item), self._vote("b", item)])
        self.assertEqual(result.status, "committed")

    def test_tie_is_unresolved(self):
        amber = hypothesis("h:a", "amber", 0.8)
        violet = hypothesis("h:v", "violet", 0.8)
        result = structured_consensus([self._vote("a", amber), self._vote("b", violet)])
        self.assertEqual(result.status, "unresolved")

    def test_low_confidence_abstains(self):
        item = hypothesis("h:1", "amber", 0.3)
        result = structured_consensus([self._vote("a", item), self._vote("b", item)])
        self.assertEqual(result.status, "abstained")
