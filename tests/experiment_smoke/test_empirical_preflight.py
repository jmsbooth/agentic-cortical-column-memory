"""Qualify the gate, not the statistical study."""
import copy
import json
import unittest
from pathlib import Path

from evaluation.empirical.preflight import assess_configuration, require_qualified_run, validate_visible_source

ROOT = Path(__file__).resolve().parents[2]


class PreflightTests(unittest.TestCase):
    def test_smoke_is_not_empirical(self):
        config = {'run_kind': 'smoke', 'model': {'family': 'symbolic-smoke-adapter', 'version': 'toy-symbolic-v0.1.0'}, 'strategies': ['M6']}
        report = assess_configuration(config, root=ROOT)
        self.assertTrue(report['ok'], report['checks'])
        self.assertFalse(report['eligible_for_empirical'])
        self.assertEqual(report['result_classification'], 'software_validation_only')

    def test_registered_toy_and_placeholder_baselines_blocked(self):
        config = {'run_kind': 'registered', 'model': {'family': 'symbolic-smoke-adapter', 'version': 'toy-symbolic-v0.1.0'}, 'strategies': ['M0', 'M3', 'M5', 'M6']}
        report = assess_configuration(config, root=ROOT)
        self.assertFalse(report['ok'])
        failures = [x['id'] for x in report['checks'] if x['status'] == 'blocked']
        self.assertIn('baseline_fidelity', failures)
        self.assertIn('real_model_required', failures)
        self.assertIn('registered_runner_qualified', failures)
        with self.assertRaises(ValueError):
            require_qualified_run(config, root=ROOT)

    def test_real_model_still_blocked_until_fidelity_gate(self):
        config = {'run_kind': 'confirmatory', 'model': {'family': 'model', 'version':'real-checkpoint'}, 'strategies':['M0','M6']}
        report = assess_configuration(config, root=ROOT)
        self.assertFalse(report['ok'])
        failures = [x['id'] for x in report['checks'] if x['status'] == 'blocked']
        self.assertNotIn('real_model_required', failures)
        self.assertIn('baseline_fidelity', failures)

    def test_source_allowlist_enforced(self):
        self.assertEqual(validate_visible_source(ROOT), [])

    def test_protocol_integrity_check(self):
        config = {'run_kind': 'smoke', 'model': {'family':'legacy'}, 'strategies':[]}
        report = assess_configuration(config, root=ROOT)
        self.assertIn({'id':'protocol_integrity','status':'pass', 'detail': next(a['detail'] for a in report['checks'] if a['id']=='protocol_integrity')},report['checks'])


if __name__ == '__main__':
    unittest.main()
