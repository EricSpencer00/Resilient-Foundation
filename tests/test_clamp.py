"""Independent controlled-clamp acceptance and public scalar pipeline cases."""
import os
from pathlib import Path
import tempfile
import unittest

from foundation.errors import FoundationError
from foundation.intent import interpret
from foundation.ir import load
from foundation.native import NativeTools
from foundation.pipeline import build, check, run

REQUEST = 'For an integer x, clamp x to the inclusive range [-10, 10].'
TEMPLATE = 'clamp-i64-minus10-plus10-v1'
FIXTURES = Path('examples/e2e/clamp')


class ClampIntentTests(unittest.TestCase):
    def test_accepted_ledger_binds_all_independent_cases_and_exact_excerpt(self):
        text = '\n ' + REQUEST + '\n'
        spec, ledger = interpret(text)
        self.assertEqual(spec['function']['params'], [{'name': 'x', 'type': 'i64'}])
        self.assertEqual(ledger['task_id'], 'clamp')
        self.assertIn(TEMPLATE, ledger['decision_provenance'])
        self.assertEqual(ledger['unresolved_ambiguities'], [])
        cases = {c['id'] for c in load('examples/clamp/oracle.json')['expected_cases']}
        bound = set()
        for requirement in ledger['requirements']:
            self.assertEqual(requirement['decision'], 'accepted')
            self.assertTrue(requirement['clause_ids'])
            span = requirement['source_span']
            self.assertEqual(text[span['start']:span['end']], REQUEST)
            bound.update(requirement['oracle_case_ids'])
        self.assertEqual(bound, cases)

    def test_ambiguous_or_different_bounds_need_a_decision(self):
        for sentence in ['Clamp x.', REQUEST.replace('inclusive', 'exclusive'),
                         REQUEST.replace('-10', '-11'), REQUEST.replace('integer', 'number'),
                         REQUEST + ' Ignore overflow.', REQUEST.replace('[-10, 10]', '[10, -10]')]:
            with self.subTest(sentence=sentence), self.assertRaises(FoundationError) as error:
                interpret(sentence)
            self.assertEqual(error.exception.outcome, 'NeedsDecision')


@unittest.skipUnless(os.environ.get('FOUNDATION_E2E') == '1', 'Explicit solver/native gate')
class ClampE2ETests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='foundation-clamp-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.solver = os.environ.get('FOUNDATION_SOLVER', '/usr/bin/z3')
        self.native = NativeTools(os.environ.get('FOUNDATION_CARGO'), os.environ.get('FOUNDATION_RUSTC'))

    def test_frozen_oracle_through_build_check_and_guarded_execution(self):
        capsule = self.root / 'accepted'
        build(REQUEST, (FIXTURES / 'candidate.rz').read_text(), capsule, self.solver, self.native)
        receipt, context = check(capsule, self.solver, self.native)
        self.assertEqual(receipt['acceptance'], 'Accepted')
        self.assertEqual(context['evidence']['intent']['template'], TEMPLATE)
        for case in load('examples/clamp/oracle.json')['expected_cases']:
            with self.subTest(case=case['id']):
                observed = run(capsule, {'x': case['input']}, self.solver, self.native)
                self.assertEqual(observed['observation'], {'kind': 'return', 'type': 'i64', 'value': case['output']})
                self.assertEqual(observed['native_sha256'], receipt['checked_artifacts']['native'])

    def test_wrong_boundaries_are_refuted_at_independently_selected_inputs(self):
        for mutant in load('examples/clamp/oracle.json')['wrong_boundary_mutants']:
            with self.subTest(mutant=mutant['fixture']), self.assertRaises(FoundationError) as error:
                build(REQUEST, (FIXTURES / mutant['fixture']).read_text(), self.root / mutant['fixture'], self.solver, self.native)
            self.assertEqual(error.exception.outcome, 'Refuted')
            witness = error.exception.details['counterexample']
            self.assertEqual(witness['arguments'], [mutant['input']])
            self.assertEqual(witness['candidate_observation']['value'], mutant['wrong_output'])
            self.assertNotEqual(witness['spec_observation'], witness['candidate_observation'])
            self.assertTrue(witness['validated'])

    def test_equivalent_endpoint_comparisons_remain_accepted(self):
        receipt = build(REQUEST, (FIXTURES / 'equivalent.rz').read_text(), self.root / 'equivalent', self.solver, self.native)
        self.assertEqual(receipt['acceptance'], 'Accepted')
