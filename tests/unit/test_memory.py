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

    def test_history_and_current_state_are_separate(self):
        store = MemoryStore()
        old = Observation(
            "obs:old", "owner is X", "frame:test", "origin", "ticket:test", 0, 1.0, "run:test",
            valid_from="2026-01-01T00:00:00Z", valid_to="2026-02-01T00:00:00Z",
        )
        new = Observation(
            "obs:new", "owner is Y", "frame:test", "origin", "ticket:test", 1, 1.0, "run:test",
            valid_from="2026-02-01T00:00:00Z",
        )
        store.write(old)
        store.write(new)
        self.assertEqual(store.historical("frame:test", at_time="2026-01-15T00:00:00Z")[0].object_id, "obs:old")
        self.assertEqual(store.current("frame:test")[0].object_id, "obs:new")
        self.assertEqual(len(store.all()), 2)

    def test_supersession_is_append_only(self):
        store = MemoryStore()
        old = self._observation("obs:old")
        new = self._observation("obs:new")
        store.write(old)
        store.write(new)
        store.supersede("obs:old", "obs:new")
        self.assertEqual(store.get("obs:old"), old)
        self.assertEqual([item.object_id for item in store.current("frame:test")], ["obs:new"])
