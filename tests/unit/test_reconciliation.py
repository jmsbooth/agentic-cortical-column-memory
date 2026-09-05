import unittest

from ccm.consensus import reconcile_hypotheses
from ccm.schemas.models import Hypothesis


class ReconciliationTests(unittest.TestCase):
    def _hypothesis(self, hypothesis_id, claim, frame="frame", location="origin"):
        return Hypothesis(hypothesis_id, claim, frame, location, (), "model:test", 0.8, 0.2)

    def test_agreement_is_not_forced_vote(self):
        result = reconcile_hypotheses((self._hypothesis("a", "amber"), self._hypothesis("b", "amber")))
        self.assertEqual(result.status, "agreement")
        self.assertEqual(result.compatible_groups, (("a", "b"),))

    def test_complementary_states_are_distinguished_from_conflict(self):
        result = reconcile_hypotheses((
            self._hypothesis("a", "amber", location="actor"),
            self._hypothesis("b", "indigo", location="resource"),
        ))
        self.assertEqual(result.status, "complementary")

    def test_same_location_conflict_remains_unresolved(self):
        result = reconcile_hypotheses((self._hypothesis("a", "amber"), self._hypothesis("b", "indigo")))
        self.assertEqual(result.status, "contradiction")
        self.assertEqual(result.unresolved_ids, ("a", "b"))
