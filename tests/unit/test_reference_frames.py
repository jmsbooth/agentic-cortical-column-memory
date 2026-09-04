import unittest

from ccm.reference_frames.core import FrameError, ReferenceFrameGraph
from ccm.schemas.models import Observation, ReferenceFrame, Transition


class ReferenceFrameTests(unittest.TestCase):
    def setUp(self):
        self.frame = ReferenceFrame(
            "frame:test", "conceptual", "origin", "origin",
            (Transition("inspect", "origin", "inspected"),),
        )

    def test_valid_transition_and_prediction(self):
        graph = ReferenceFrameGraph(self.frame)
        self.assertEqual(graph.predict_next_location("inspect"), "inspected")
        self.assertEqual(graph.transition("inspect").state, "inspected")

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(FrameError):
            ReferenceFrameGraph(self.frame).transition("unknown")

    def test_location_persists_and_wrong_frame_is_rejected(self):
        graph = ReferenceFrameGraph(self.frame)
        graph.transition("inspect")
        observation = Observation("obs", "evidence", "frame:test", "inspected", "tool:test", 0, 1.0, "run:test")
        graph.attach_observation(observation)
        wrong = Observation("wrong", "evidence", "frame:other", "inspected", "tool:test", 1, 1.0, "run:test")
        with self.assertRaises(FrameError):
            graph.attach_observation(wrong)
