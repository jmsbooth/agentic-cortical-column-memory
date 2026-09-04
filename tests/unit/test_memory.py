import unittest

from ccm.memory.store import MemoryConflict, MemoryStore
from ccm.schemas.models import Observation


class MemoryTests(unittest.TestCase):
    def _observation(self, object_id="obs:1", source="environment:test"):
        return Observation(object_id, "fact", "frame:test", "origin", source, 0, 1.0, "run:test")

    def test_provenance_and_immutable_duplicate_handling(self):
        store = MemoryStore()
        observation = self._observation()
        store.write(observation)
        with self.assertRaises(MemoryConflict):
            store.write(observation)
        self.assertEqual(store.get("obs:1").provenance, "run:test")

    def test_model_generated_external_observation_is_rejected(self):
        with self.assertRaises(ValueError):
            self._observation(source="model:fake")

    def test_conflicting_observations_remain_distinct(self):
        store = MemoryStore()
        store.write(self._observation("obs:a"))
        store.write(self._observation("obs:b"))
        self.assertEqual(len(store.all()), 2)
