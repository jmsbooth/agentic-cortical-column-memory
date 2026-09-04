import unittest

from ccm.active_evidence.policy import ActiveEvidencePolicy
from ccm.schemas.models import EvidenceAction, Hypothesis, Observation


class ActiveEvidenceTests(unittest.TestCase):
    def test_selects_information_gain_per_cost_and_respects_budget(self):
        obs = Observation("obs", "evidence", "frame:test", "origin", "environment:test", 0, 1.0, "run:test")
        h = Hypothesis("h", "amber", "frame:test", "origin", (), "model:test", 0.5, 0.5)
        cheap = EvidenceAction("cheap", "cheap", ("h",), obs, 0.4, 1.0)
        decisive = EvidenceAction("decisive", "decisive", ("h",), obs, 1.0, 1.0)
        policy = ActiveEvidencePolicy()
        self.assertEqual(policy.select([h], [cheap, decisive], used_action_ids=set(), budget_remaining=1).action_id, "decisive")
        self.assertIsNone(policy.select([h], [cheap], used_action_ids={"cheap"}, budget_remaining=1))
