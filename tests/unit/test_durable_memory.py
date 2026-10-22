"""SQLite memory lifecycle and temporal invariants for CCM-EMP-002 Phase 1B."""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ccm.memory.durable import SQLiteMemoryStore
from ccm.memory.store import MemoryConflict
from ccm.schemas.models import Observation
from ccm.empirical.contracts import BoundaryViolation, ModelVisibleCase, VisibleObservation


T0 = "2026-01-01T00:00:00Z"
T1 = "2026-02-01T00:00:00Z"
T2 = "2026-03-01T00:00:00Z"


def observation(name: str, *, content: str | None = None, location: str = "resource",
                sequence: int = 0, start: str | None = None, end: str | None = None,
                observed_at: str | None = None) -> Observation:
    return Observation(
        object_id=name, content=content or name, frame_id="frame:entity", location=location,
        source="source:external", sequence=sequence, confidence=1.0, provenance="event:source",
        valid_from=start, valid_to=end, observed_at=observed_at,
        relations=("source:relation",),
    )


class DurableMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "memory.sqlite3"

    def tearDown(self) -> None:
        self.dir.cleanup()

    def open(self, agent: str = "agent-A", column: str = "column-1") -> SQLiteMemoryStore:
        return SQLiteMemoryStore(self.path, agent_id=agent, column_id=column)

    def test_cross_session_restart_preserves_original_observations(self):
        with self.open() as store:
            value = observation("obs-a",content="historical note")
            store.write(value)
            digest = store.snapshot_digest()
            self.assertEqual(store.stats().write_count, 1)
        with self.open() as second:
            self.assertEqual(second.get("obs-a"), value)
            self.assertEqual(second.snapshot_digest(), digest)
            self.assertEqual(len(second.all()), 1)
            self.assertEqual(second.stats().write_count, 0)

    def test_per_agent_and_column_isolation_with_same_observation_ids(self):
        with self.open("alice","identity") as a, self.open("bob","identity") as b, self.open("alice","device") as c:
            a.write(observation("same",content="alice identity"))
            b.write(observation("same",content="bob identity"))
            c.write(observation("same",content="alice device"))
            self.assertNotEqual(a.get("same"),b.get("same"))
            self.assertNotEqual(a.get("same"),c.get("same"))
            self.assertEqual(len(a.all()),1)
            self.assertEqual(len(b.all()),1)
            self.assertEqual(len(c.all()),1)
            with self.assertRaises(KeyError):a.get("foreign")

    def test_duplicate_id_rejected_atomically(self):
        with self.open() as store:
            store.write(observation("one"))
            with self.assertRaises(MemoryConflict):
                store.write_many((observation("two"),observation("one",content="evil")))
            self.assertEqual([o.object_id for o in store.all()],["one"])

    def test_pending_transaction_crash_rollback_preserves_history(self):
        with self.open() as store:
            store.write(observation("prior"))
            with self.assertRaises(sqlite3.IntegrityError):
                # Database FK guards cross-namespaced references even under direct SQL.
                store._conn.execute("INSERT INTO supersessions(agent_id,column_id,old_id,new_id,effective_at,recorded_at) VALUES(?,?,?,?,?,?)",("agent-A","column-1","prior","ghost",T1,T2))
        with self.open() as store:
            self.assertEqual([o.object_id for o in store.all()],["prior"])
            self.assertEqual(store.supersession_map(),{})

    def test_historical_queries_pre_and_post_supersession(self):
        with self.open() as store:
            store.write(observation("old",content="owner X",sequence=1,start=T0))
            store.write(observation("new",content="owner Y",sequence=2,start=T1))
            store.supersede("old","new",effective_at=T1)
            self.assertEqual({o.object_id for o in store.current("frame:entity",at_time="2026-01-15T00:00:00Z")},{"old"})
            self.assertEqual({o.object_id for o in store.current("frame:entity",at_time="2026-02-15T00:00:00Z")},{"new"})
            self.assertEqual({o.object_id for o in store.historical("frame:entity",at_time="2026-02-15T00:00:00Z")},{"old","new"})

    def test_supersession_is_restored_after_reopen(self):
        with self.open() as store:
            store.write(observation("x",start=T0))
            store.write(observation("y",sequence=1,start=T1))
            store.supersede("x","y",effective_at=T1)
            digest=store.snapshot_digest()
        with self.open() as store:
            self.assertEqual(store.supersession_map(),{"x":"y"})
            self.assertEqual(store.snapshot_digest(),digest)
            self.assertEqual([x.object_id for x in store.current("frame:entity")],["y"])

    def test_undated_supersession_does_not_rewrite_historical_reality(self):
        with self.open() as store:
            store.write(observation("old"))
            store.write(observation("new",sequence=1))
            store.supersede("old","new")
            self.assertEqual({o.object_id for o in store.current("frame:entity",at_time=T0)},{"old","new"})
            self.assertEqual({o.object_id for o in store.current("frame:entity")},{"new"})

    def test_late_arrival_reconstructs_historical_state(self):
        with self.open() as store:
            store.write(observation("latest",sequence=9,start=T2))
        with self.open() as store:
            store.write(observation("late",sequence=10,start=T0,end=T1))
            self.assertEqual([o.object_id for o in store.current("frame:entity",at_time="2026-01-15T00:00:00Z")],["late"])
            self.assertEqual([o.object_id for o in store.current("frame:entity")],["latest"])

    def test_conflicting_unsuperseded_states_remain_visible(self):
        with self.open() as store:
            store.write(observation("a",content="status open",start=T0))
            store.write(observation("b",content="status closed",sequence=1,start=T0))
            self.assertEqual({o.object_id for o in store.current("frame:entity")},{"a","b"})

    def test_supersession_rejects_cycle_and_branching(self):
        with self.open() as store:
            for n in ("a","b","c"):
                store.write(observation(n))
            store.supersede("a","b")
            with self.assertRaises(MemoryConflict):store.supersede("b","a")
            with self.assertRaises(MemoryConflict):store.supersede("a","c")
            self.assertEqual(store.supersession_map(),{"a":"b"})

    def test_supersession_rejects_foreign_location_and_missing_object(self):
        with self.open() as store:
            store.write(observation("a",location="a"))
            store.write(observation("b",location="b"))
            with self.assertRaises(MemoryConflict):store.supersede("a","b")
            with self.assertRaises(KeyError):store.supersede("a","does-not-exist")

    def test_supersession_rejects_effective_time_before_original(self):
        with self.open() as store:
            store.write(observation("a",start=T1))
            store.write(observation("b",start=T0))
            with self.assertRaises(MemoryConflict):store.supersede("a","b",effective_at=T0)

    def test_observation_immutable_even_if_python_attributes_are_frozen(self):
        with self.open() as store:
            old=observation("a")
            store.write(old)
            with self.assertRaises(MemoryConflict):store.write(replace(old,content="new data"))
            self.assertEqual(store.get("a"),old)

    def test_timestamp_validation_fails_closed(self):
        with self.open() as store:
            for wrong in ("not-a-date","2026-01-01T00:00:00","2026-13-01T00:00:00Z"):
                with self.subTest(wrong=wrong),self.assertRaises(MemoryConflict):
                    store.write(observation("invalid",start=wrong))
            self.assertEqual(store.all(),())

    def test_invalid_interval_rejected(self):
        with self.open() as store:
            with self.assertRaises((MemoryConflict, ValueError)):
                store.write(observation("invalid",start=T2,end=T1))

    def test_model_generated_external_facts_rejected(self):
        with self.open() as store:
            with self.assertRaises((MemoryConflict, ValueError)):
                value=replace(observation("fake"),source="model:unverified")
                store.write(value)

    def test_embedded_supersession_not_accepted(self):
        with self.open() as store:
            value=replace(observation("old"),superseded_by="future-id")
            with self.assertRaises(MemoryConflict):store.write(value)

    def test_schema_version_rejection(self):
        with self.open() as store:store.write(observation("a"))
        with sqlite3.connect(self.path) as db:db.execute("PRAGMA user_version=777")
        with self.assertRaises(MemoryConflict):self.open()

    def test_gold_field_object_rejected_by_durable_ingest(self):
        with self.open() as store:
            class Oracle:
                gold_answer="secret"
            with self.assertRaises(BoundaryViolation):store.write_visible_case(Oracle())

    def test_model_visible_ingest_atomic_and_persistent(self):
        case_id="case:1234567890abcdef"
        history=(VisibleObservation(f"{case_id}:obs:1","device was issued","%s:src:1"%case_id,"frame:entity","resource",T0),)
        case=ModelVisibleCase(case_id,"which device?",history,(),("A","B"),(f"{case_id}:src:1",),256)
        with self.open() as store:store.write_visible_case(case)
        with self.open() as store:
            obj=store.get(f"{case_id}:obs:1")
            self.assertEqual(obj.content,"device was issued")
            self.assertNotIn("gold_answer",str(obj.to_dict()))
            self.assertEqual(obj.source,f"{case_id}:src:1")

    def test_bitemporal_as_known_before_late_ingest_excludes_future_knowledge(self):
        with self.open() as store:
            earlier = replace(observation("old",start=T0),recorded_at=T0)
            later = replace(observation("late",sequence=4,start=T0),recorded_at=T2)
            store.write(earlier)
            store.write(later)
            self.assertEqual(
                [o.object_id for o in store.historical("frame:entity",at_time=T1,known_at=T1)],
                ["old"],
            )
            self.assertEqual(
                {o.object_id for o in store.historical("frame:entity",at_time=T1,known_at=T2)},
                {"old","late"},
            )

    def test_supersession_recorded_later_is_not_known_earlier(self):
        with self.open() as store:
            store.write(replace(observation("a",start=T0),recorded_at=T0))
            store.write(replace(observation("b",sequence=2,start=T1),recorded_at=T1))
            store.supersede("a","b",effective_at=T1,recorded_at=T2)
            self.assertEqual(
                {o.object_id for o in store.current("frame:entity",at_time=T2,known_at=T1)},
                {"a","b"},
            )
            self.assertEqual(
                {o.object_id for o in store.current("frame:entity",at_time=T2,known_at=T2)},
                {"b"},
            )

    def test_stale_or_corrupt_schema_metadata_is_detected(self):
        with self.open() as store:store.write(observation("a"))
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("DROP TABLE operations")
            db.commit()
        with self.assertRaises(MemoryConflict):self.open()

    def test_transaction_rejects_foreign_namespace_replacement(self):
        with self.open("alice") as a, self.open("bob") as b:
            a.write(observation("origin"))
            b.write(observation("replacement"))
            with self.assertRaises(KeyError):a.supersede("origin","replacement")
            self.assertEqual(a.supersession_map(),{})

    def test_observation_payload_integrity_checked_on_read(self):
        with self.open() as store:
            store.write(observation("a"))
            store._conn.execute(
                "UPDATE observations SET payload='\"tampered\"' WHERE agent_id=? AND column_id=? AND object_id=?",
                (store.agent_id,store.column_id,"a"),
            )
            with self.assertRaises(MemoryConflict):store.get("a")

    def test_failed_batch_never_commits_any_partial_rows(self):
        with self.open() as store:
            obs_a = observation("a",sequence=1)
            obs_b = observation("b",sequence=2)
            with self.assertRaises(MemoryConflict):
                store.write_many((obs_a,obs_b,replace(obs_a,sequence=3)))
        with self.open() as store:
            self.assertEqual(store.all(),())

    def test_storage_measurement_is_nonzero_after_writes(self):
        with self.open() as store:
            store.write(observation("a"))
            self.assertGreater(store.stats().storage_bytes,0)
            self.assertGreater(store.stats().write_wall_ns,0)
            self.assertGreater(store.stats().write_count,0)

    def test_closed_store_fails_closed(self):
        store=self.open()
        store.close()
        with self.assertRaises(MemoryConflict):store.write(observation("new"))


if __name__ == "__main__":
    unittest.main()
