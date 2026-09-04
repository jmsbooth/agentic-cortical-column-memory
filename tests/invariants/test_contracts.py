import unittest

from ccm.schemas.models import Hypothesis, Vote


class ContractInvariantTests(unittest.TestCase):
    def test_vote_references_existing_hypothesis_identity(self):
        item = Hypothesis("h", "claim", "frame", "origin", (), "model:test", 0.8, 0.2)
        with self.assertRaises(ValueError):
            Vote("v", "column", "other", item, 0.8)
