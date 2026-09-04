import json
import tempfile
import unittest
from pathlib import Path

from experiments.runners.run import run_config


class RunnerSmokeTests(unittest.TestCase):
    def test_runner_emits_manifest_and_complete_records(self):
        config = json.loads(Path("experiments/configs/smoke_v0.1.0.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            raw_path, manifest_path = run_config(config, Path(directory), Path(directory) / "manifests")
            self.assertTrue(raw_path.exists())
            self.assertTrue(manifest_path.exists())
            record = json.loads(raw_path.read_text().splitlines()[0])
            self.assertEqual(record["experiment_id"], config["experiment_id"])
            self.assertIn("trace", record)
            self.assertIn("resources", record)
