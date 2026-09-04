import unittest

from experiments.tasks.synthetic_world import build_suite


class DeterminismTests(unittest.TestCase):
    def test_seeded_task_generation_is_stable(self):
        left = build_suite(7, ["persistent_memory", "pure_reasoning"], 2)
        right = build_suite(7, ["persistent_memory", "pure_reasoning"], 2)
        self.assertEqual([task.task_id for task in left], [task.task_id for task in right])
        self.assertEqual([task.answer for task in left], [task.answer for task in right])
