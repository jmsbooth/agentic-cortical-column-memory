"""Memory lifecycle contract for repeated agent invocations.

This test is intended for the GitHub checkout with the real CCMEngine and
legacy ToyModel. It is not runnable in the minimal local Phase 1B scaffold.
"""
import tempfile
import unittest
from pathlib import Path
from ccm.memory.durable import SQLiteMemoryStore
from ccm.schemas.models import Observation
from ccm.orchestration.engine import CCMEngine
from ccm.column.core import Column
from ccm.schemas.models import ReferenceFrame, Transition, Hypothesis


class PersistentEngineTests(unittest.TestCase):
    def test_engine_can_reuse_store_across_calls_without_losing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/"agent.db"
            frame=ReferenceFrame("frame:engine","test","origin","origin")
            hypotheses=(
                Hypothesis("h:a","answer-a",frame.frame_id,"origin",(),"task:synthetic",0.5,0.5),
            )
            def propose(task_id, specialization, observations, candidates, index):
                return candidates[0]
            o1=Observation("obs:one","first event",frame.frame_id,"origin","env:test",0,1.0,"prov:first")
            o2=Observation("obs:two","second event",frame.frame_id,"origin","env:test",1,1.0,"prov:second")
            with SQLiteMemoryStore(db,agent_id="agent-a",column_id="local") as store:
                def make_engine():
                    return CCMEngine(frame=frame,columns=[Column("col-a",frame,"domain")],
                        propose=propose,min_quorum=1,max_steps=1,allow_active=False,
                        memory_factory=lambda:store)
                make_engine().solve(task_id="first",initial_observations=(o1,),hypotheses=hypotheses,
                    actions=(),observe_action=lambda _:o1)
                make_engine().solve(task_id="second",initial_observations=(o1,o2),hypotheses=hypotheses,
                    actions=(),observe_action=lambda _:o2)
                self.assertEqual({o.object_id for o in store.all()},{"obs:one","obs:two"})
            with SQLiteMemoryStore(db,agent_id="agent-a",column_id="local") as reopened:
                self.assertEqual({o.object_id for o in reopened.all()},{"obs:one","obs:two"})


if __name__=="__main__":unittest.main()
