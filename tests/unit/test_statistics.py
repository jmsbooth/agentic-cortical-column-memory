import unittest

from evaluation.statistics.bootstrap import bootstrap_mean_difference, holm_adjust


class StatisticsTests(unittest.TestCase):
    def test_bootstrap_is_deterministic_and_bounded(self):
        first = bootstrap_mean_difference([1, 1, 0], [0, 1, 0], resamples=200, seed=3)
        second = bootstrap_mean_difference([1, 1, 0], [0, 1, 0], resamples=200, seed=3)
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0.333333)
        self.assertLessEqual(first[1], first[0])
        self.assertGreaterEqual(first[2], first[0])

    def test_holm_preserves_order(self):
        self.assertEqual(holm_adjust([0.01, 0.04, 0.2]), (0.03, 0.08, 0.2))
