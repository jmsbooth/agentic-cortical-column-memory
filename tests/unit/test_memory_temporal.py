"""Temporal current-state and uncertainty regression for the legacy RAM backend."""
import unittest
from ccm.memory.store import MemoryStore, MemoryConflict
from ccm.schemas.models import Observation


def obs(oid, seq=0, start=None, end=None, recorded=None, location="resource"):
    return Observation(oid,oid,"f",location,"source",seq,1.0,"provenance",valid_from=start,valid_to=end,recorded_at=recorded)


class InMemoryTemporalTests(unittest.TestCase):
    def test_superseded_today_does_not_erase_past(self):
        s=MemoryStore()
        s.write(obs("a",start="2026-01-01T00:00:00Z"))
        s.write(obs("b",seq=1,start="2026-02-01T00:00:00Z"))
        s.supersede("a","b")
        self.assertEqual([x.object_id for x in s.current("f",at_time="2026-01-15T00:00:00Z")],["a"])
        self.assertEqual([x.object_id for x in s.current("f",at_time="2026-03-01T00:00:00Z")],["b"])

    def test_conflicting_observations_do_not_silently_collapse(self):
        s=MemoryStore()
        s.write(obs("a"));s.write(obs("b",seq=1))
        self.assertEqual({x.object_id for x in s.current("f")},{"a","b"})

    def test_unknown_effective_date_retains_historical_ambiguity(self):
        s=MemoryStore()
        s.write(obs("a"));s.write(obs("b",seq=1));s.supersede("a","b")
        self.assertEqual(s.current("f",at_time="2026-03-01T00:00:00Z"),())
        self.assertEqual([x.object_id for x in s.current("f")],["b"])

    def test_bitemporal_cutoff_not_future(self):
        s=MemoryStore()
        s.write(obs("a",start="2026-01-01T00:00:00Z",recorded="2026-01-01T00:00:00Z"))
        s.write(obs("b",seq=1,start="2026-02-01T00:00:00Z",recorded="2026-02-01T00:00:00Z"))
        s.supersede("a","b",effective_at="2026-02-01T00:00:00Z",recorded_at="2026-03-01T00:00:00Z")
        self.assertEqual({x.object_id for x in s.current("f",at_time="2026-03-02T00:00:00Z",known_at="2026-02-15T00:00:00Z")},{"a","b"})
        self.assertEqual([x.object_id for x in s.current("f",at_time="2026-03-02T00:00:00Z",known_at="2026-03-02T00:00:00Z")],["b"])

    def test_future_effective_supersession_retains_old_current_state(self):
        s = MemoryStore()
        s.write(obs("old", start="2025-01-01T00:00:00Z"))
        s.write(obs("replacement", seq=1, start="2035-01-01T00:00:00Z"))
        s.supersede("old", "replacement", effective_at="2035-01-01T00:00:00Z")
        self.assertEqual([x.object_id for x in s.current("f")], ["old"])
        self.assertEqual([x.object_id for x in s.current("f", at_time="2034-01-01T00:00:00Z")], ["old"])
        self.assertEqual([x.object_id for x in s.current("f", at_time="2036-01-01T00:00:00Z")], ["replacement"])

    def test_supersession_rejects_cycles_and_foreign_frame(self):
        s=MemoryStore()
        s.write(obs("a"));s.write(obs("b"));s.write(obs("c",location="other"))
        s.supersede("a","b")
        with self.assertRaises(MemoryConflict):s.supersede("b","a")
        with self.assertRaises(MemoryConflict):s.supersede("b","c")

if __name__=="__main__":unittest.main()
