import unittest

from experiments.baselines.strategies import run_strategy
from experiments.tasks.synthetic_world import make_task


class EngineIntegrationTests(unittest.TestCase):
    def test_active_task_gathers_evidence_and_traces_it(self):
        task = make_task("active_evidence", 0, 7)
        trace, meter = run_strategy(task, "M6", 7)
        meter.finish()
        self.assertEqual(trace["status"], "committed")
        self.assertEqual(trace["answer"], task.answer)
        self.assertTrue(trace["actions"])
        self.assertTrue(trace["memory"])

    def test_incomplete_task_does_not_force_consensus(self):
        task = make_task("incomplete_information", 0, 7)
        trace, meter = run_strategy(task, "M6", 7)
        meter.finish()
        self.assertIn(trace["status"], {"abstained", "unresolved"})

    def test_conflicting_evidence_does_not_collapse_to_majority(self):
        task = make_task("conflicting_evidence", 0, 7)
        trace, meter = run_strategy(task, "M6", 7)
        meter.finish()
        self.assertIn(trace["status"], {"abstained", "unresolved"})
