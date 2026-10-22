"""Negative and metamorphic tests. These do not score model capability."""
import json
import unittest
from dataclasses import replace
from pathlib import Path

from ccm.adapters.empirical import EmpiricalLLMAdapter
from ccm.empirical.contracts import BoundaryViolation, ModelVisibleCase, VisibleAction, VisibleObservation
from ccm.empirical.operations import plan_memory_writes, plan_memory_recall
from evaluation.empirical.oracles import EvaluatorOnlyCase
from experiments.empirical.cases import make_boundary_fixture


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.visible, self.oracle = make_boundary_fixture(102, 7)

    def test_gold_change_does_not_change_visible_payload_or_observation_ids(self):
        before = self.visible.to_json()
        altered = replace(self.oracle, gold_answer="NotTaylor", accepted_answers=("NotTaylor",))
        self.assertNotEqual(self.oracle.gold_answer, altered.gold_answer)
        self.assertEqual(self.visible.to_json(), before)
        self.assertEqual([x.observation_id for x in self.visible.history],
                         [x.observation_id for x in ModelVisibleCase.from_json(before).history])

    def test_gold_mutation_preserves_memory_write_and_recall_plans(self):
        writes_before = plan_memory_writes(self.visible)
        query_before = plan_memory_recall(self.visible)
        oracle_after = replace(self.oracle, gold_answer="Mutated", accepted_answers=("Mutated",))
        self.assertNotEqual(oracle_after.gold_answer, self.oracle.gold_answer)
        self.assertEqual(plan_memory_writes(self.visible), writes_before)
        self.assertEqual(plan_memory_recall(self.visible), query_before)
        with self.assertRaises(BoundaryViolation):
            plan_memory_writes(self.oracle)
        with self.assertRaises(BoundaryViolation):
            plan_memory_recall(self.oracle)

    def test_candidate_order_independent_of_gold_and_not_always_gold_first(self):
        found_first, found_second = False, False
        for number in range(24):
            visible, oracle = make_boundary_fixture(100 + number, 1)
            found_first |= visible.choices[0] == oracle.gold_answer
            found_second |= visible.choices[-1] == oracle.gold_answer
        self.assertTrue(found_first and found_second)

    def test_model_payload_excludes_evaluator_metadata(self):
        serialized = self.visible.to_json()
        self.assertNotIn('gold_answer', serialized)
        self.assertNotIn('ground_truth', serialized)
        self.assertNotIn('supports=', serialized)
        self.assertNotIn('scoring_metadata', serialized)
        self.assertNotIn('hidden_task_family', serialized)
        self.assertNotIn('valid_evidence_paths', serialized)

    def test_extra_gold_field_fails_closed(self):
        injected = {**self.visible.to_dict(), 'ground_truth': 'canary'}
        with self.assertRaises(BoundaryViolation):
            ModelVisibleCase.from_dict(injected)

    def test_duplicate_json_keys_fail_closed(self):
        payload = self.visible.to_json().replace('"case_id":', '"case_id":"case:deadbeefdeadbeef","case_id":', 1)
        with self.assertRaises(BoundaryViolation):
            ModelVisibleCase.from_json(payload)

    def test_support_marker_and_evaluator_canary_rejected(self):
        for content in ('supports=Taylor', 'ground_truth: Taylor', '__EVALUATOR_ONLY_LABEL_CANARY'):
            altered = replace(self.visible.history[0], content=content)
            with self.subTest(content=content), self.assertRaises(BoundaryViolation):
                replace(self.visible, history=(altered, self.visible.history[1]))

    def test_cross_case_ids_and_source_tamper_rejected(self):
        foreign, _ = make_boundary_fixture(222, 5)
        with self.assertRaises(BoundaryViolation):
            replace(self.visible, history=(foreign.history[0],))
        with self.assertRaises(BoundaryViolation):
            replace(self.visible, allowed_source_ids=(foreign.history[0].source_id,))
        with self.assertRaises(BoundaryViolation):
            replace(self.visible, history=(replace(self.visible.history[0], source_id=foreign.history[0].source_id), self.visible.history[1]))

    def test_foreign_action_is_blocked(self):
        foreign, _ = make_boundary_fixture(122, 3)
        with self.assertRaises(BoundaryViolation):
            replace(self.visible, available_actions=(VisibleAction(foreign.case_id+':action:01', 'look up', 'tool'),))

    def test_real_model_adapter_sees_only_visible_payload(self):
        captured = []
        def complete(payload):
            captured.append(payload)
            return json.dumps({'answer': 'Taylor', 'evidence_ids': [self.visible.history[1].observation_id], 'abstained': False})
        adapter = EmpiricalLLMAdapter(complete, version='open-weight-checkpoint', backend='local-llm')
        self.assertEqual(adapter.answer_case(self.visible).answer, 'Taylor')
        self.assertEqual(captured, [self.visible.to_json()])
        with self.assertRaises(BoundaryViolation):
            adapter.answer_case(self.oracle)

    def test_model_cannot_cite_foreign_or_fabricated_evidence(self):
        adapter = EmpiricalLLMAdapter(lambda _: json.dumps({'answer':'Taylor', 'evidence_ids':['case:deadbeefdeadbeef:obs:999'], 'abstained':False}), version='checkpoint', backend='local')
        with self.assertRaises(BoundaryViolation):
            adapter.answer_case(self.visible)

    def test_adapter_rejects_symbolic_backend_and_invalid_model_reply(self):
        with self.assertRaises(BoundaryViolation):
            EmpiricalLLMAdapter(lambda _: '{}', version='toy-symbolic-v0.1.0', backend='local')
        adapter = EmpiricalLLMAdapter(lambda _: json.dumps({'answer':'Taylor', 'evidence_ids':[], 'abstained':False,'ground_truth':'Taylor'}), version='checkpoint', backend='local')
        with self.assertRaises(BoundaryViolation):
            adapter.answer_case(self.visible)

    def test_evaluator_does_not_fit_visible_contract(self):
        with self.assertRaises(BoundaryViolation):
            ModelVisibleCase.from_dict(self.oracle.__dict__)
        self.assertNotIsInstance(self.oracle, ModelVisibleCase)


if __name__ == '__main__':
    unittest.main()
