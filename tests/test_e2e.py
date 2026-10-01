"""Independent release gate. Run explicitly with FOUNDATION_E2E=1 on compute host."""
import copy
import os
import json
from pathlib import Path
import shutil
import tempfile
import subprocess
import sys
import unittest

from foundation.errors import FoundationError
from foundation.intent import SENTENCE
from foundation.ir import file_hash, identity, load, write_json
from foundation.native import NativeTools, decode
from foundation.pipeline import build, check, run
from foundation.smt import equivalence_query, solve
from foundation.source import parse_source


@unittest.skipUnless(os.environ.get('FOUNDATION_E2E') == '1', 'Explicit remote end-to-end gate')
class E2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = os.environ.get('FOUNDATION_SOLVER', '/usr/bin/z3')
        cls.native = NativeTools(os.environ.get('FOUNDATION_CARGO'), os.environ.get('FOUNDATION_RUSTC'))
        cls.scratch = tempfile.TemporaryDirectory(prefix='foundation-e2e-tests-')
        cls.root = Path(cls.scratch.name)
        cls.candidate = Path('examples/e2e/nonnegative/candidate.rz').read_text()
        cls.base = cls.root / 'accepted'
        build(SENTENCE, cls.candidate, cls.base, cls.solver, cls.native)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def copy_capsule(self):
        directory = self.root / self._testMethodName
        shutil.copytree(self.base, directory)
        return directory

    def manifest(self, directory):
        return load(directory / 'capsule.json')

    def rehash(self, directory, *names):
        evidence = self.manifest(directory)
        for name in names:
            evidence['artifact_hashes'][name] = file_hash(directory / name)
        write_json(directory / 'capsule.json', evidence)

    def assert_invalid(self, directory):
        with self.assertRaises(FoundationError) as error:
            check(directory, self.solver, self.native)
        self.assertEqual(error.exception.outcome, 'InvalidEvidence')

    def test_all_frozen_oracle_boundaries_execute(self):
        oracle = load('examples/nonnegative/oracle.json')
        for case in oracle['expected_cases']:
            with self.subTest(case=case['id']):
                execution = run(self.base, {'x': case['input']}, self.solver, self.native)
                self.assertEqual(execution['observation'], {'kind': 'return', 'type': 'i64', 'value': case['output']})
                self.assertEqual(execution['runtime_status'], 'DeployedBound')

    def test_equivalent_boundary_mutant_is_accepted(self):
        candidate = Path('examples/e2e/nonnegative/equivalent.rz').read_text()
        receipt = build(SENTENCE, candidate, self.root / 'equivalent', self.solver, self.native)
        self.assertEqual(receipt['acceptance'], 'Accepted')

    def test_wrong_branch_is_refuted_with_rust_replayed_witness(self):
        candidate = Path('examples/e2e/nonnegative/wrong-branch.rz').read_text()
        with self.assertRaises(FoundationError) as error:
            build(SENTENCE, candidate, self.root / 'wrong', self.solver, self.native)
        self.assertEqual(error.exception.outcome, 'Refuted')
        witness = error.exception.details['counterexample']
        self.assertLess(int(witness['arguments'][0]), 0)
        self.assertEqual(witness['spec_observation']['value'], '0')
        self.assertNotEqual(witness['spec_observation'], witness['candidate_observation'])
        self.assertTrue(witness['validated'])

    def test_overflow_witness_matches_independent_machine_boundary(self):
        spec, _ = parse_source('fn f(int x) -> int { if x == 9223372036854775807 { return x + 1; } else { return 0; } }')
        bad, _ = parse_source('fn f(int x) -> int { if x == 9223372036854775807 { return x; } else { return 0; } }')
        result = solve(spec, bad, self.solver)
        self.assertEqual(result['outcome'], 'Refuted')
        self.assertEqual(result['arguments'], ['9223372036854775807'])
        self.assertEqual(self.native.evaluate(spec, result['arguments'])['value'], '-9223372036854775808')

    def test_division_error_is_an_observable_difference(self):
        spec, _ = parse_source('fn f(int x) -> int { return 1 / x; }')
        bad, _ = parse_source('fn f(int x) -> int { if x == 0 { return 0; } else { return 1 / x; } }')
        result = solve(spec, bad, self.solver)
        self.assertEqual(result['outcome'], 'Refuted')
        self.assertEqual(result['arguments'], ['0'])
        self.assertEqual(self.native.evaluate(spec, ['0']), {'kind': 'error', 'error': 'DivideByZero'})
        self.assertEqual(self.native.evaluate(bad, ['0']), {'kind': 'return', 'type': 'i64', 'value': '0'})

    def test_short_circuit_does_not_create_a_phantom_division_error(self):
        spec, _ = parse_source('fn f(int x) -> bool { return false && (1 / x == 0); }')
        equivalent, _ = parse_source('fn f(int x) -> bool { return false; }')
        self.assertEqual(solve(spec, equivalent, self.solver)['outcome'], 'Proved')
        self.assertEqual(self.native.evaluate(spec, ['0']), {'kind': 'return', 'type': 'bool', 'value': False})

    def test_minimum_division_and_truncation_use_machine_semantics(self):
        for source, expected in [
            ('fn f() -> int { return -9223372036854775808 / -1; }', '-9223372036854775808'),
            ('fn f() -> int { return -7 / 3; }', '-2'),
        ]:
            spec, _ = parse_source(source)
            target, _ = parse_source('fn f() -> int { return ' + expected + '; }')
            self.assertEqual(solve(spec, target, self.solver)['outcome'], 'Proved')
            self.assertEqual(self.native.evaluate(spec, [])['value'], expected)

    def test_stale_source_is_rejected(self):
        directory = self.copy_capsule()
        (directory / 'candidate.rz').write_text(self.candidate + '\n// changed bytes\n')
        self.assert_invalid(directory)

    def test_hash_consistent_wrong_query_is_reconstructed_and_rejected(self):
        directory = self.copy_capsule()
        (directory / 'formal.smt2').write_text('(set-logic QF_BV)\n(assert false)\n(check-sat)\n')
        self.rehash(directory, 'formal.smt2')
        self.assert_invalid(directory)

    def test_forged_native_hash_cannot_authorize_different_bytes(self):
        directory = self.copy_capsule()
        (directory / 'native').write_bytes(b'forged executable')
        self.rehash(directory, 'native')
        self.assert_invalid(directory)

    def test_model_cannot_be_changed_without_matching_source(self):
        directory = self.copy_capsule()
        model = load(directory / 'candidate-ir.json')
        model['function']['body'] = {'kind': 'int', 'type': 'i64', 'value': '0'}
        write_json(directory / 'candidate-ir.json', model)
        self.rehash(directory, 'candidate-ir.json')
        evidence = self.manifest(directory)
        evidence['canonical_identities']['candidate'] = identity('program-ir', model)
        write_json(directory / 'capsule.json', evidence)
        self.assert_invalid(directory)

    def test_forged_proof_is_rerun_even_when_source_models_and_query_hashes_agree(self):
        directory = self.copy_capsule()
        source = Path('examples/e2e/nonnegative/wrong-branch.rz').read_text()
        model, source_map = parse_source(source)
        (directory / 'candidate.rz').write_text(source)
        write_json(directory / 'candidate-ir.json', model)
        write_json(directory / 'source-map.json', source_map)
        query, _ = equivalence_query(load(directory / 'spec-ir.json'), model)
        (directory / 'formal.smt2').write_text(query)
        self.rehash(directory, 'candidate.rz', 'candidate-ir.json', 'source-map.json', 'formal.smt2')
        evidence = self.manifest(directory)
        evidence['generation']['candidate_source_sha256'] = evidence['artifact_hashes']['candidate.rz']
        evidence['canonical_identities']['candidate'] = identity('program-ir', model)
        write_json(directory / 'capsule.json', evidence)
        self.assert_invalid(directory)

    def test_solver_evidence_cannot_be_promoted_to_kernel_evidence(self):
        directory = self.copy_capsule()
        evidence = self.manifest(directory)
        evidence['formal']['evidence_class'] = 'kernel_checked'
        write_json(directory / 'capsule.json', evidence)
        self.assert_invalid(directory)

    def test_changed_runtime_wrapper_is_rejected_before_compilation(self):
        directory = self.copy_capsule()
        source = (directory / 'generated.rs').read_text()
        (directory / 'generated.rs').write_text(source + '\nfn hidden() { std::process::exit(0); }\n')
        self.rehash(directory, 'generated.rs')
        self.assert_invalid(directory)

    def test_missing_solver_is_unsupported(self):
        with self.assertRaises(FoundationError) as error:
            build(SENTENCE, self.candidate, self.root / 'missing-solver', '/no/such/solver', self.native)
        self.assertEqual(error.exception.outcome, 'Unsupported')

    def test_unknown_solver_is_not_promoted_to_success(self):
        fake = self.root / 'unknown-solver'
        fake.write_text('#!/usr/bin/env python3\nprint("unknown")\n')
        fake.chmod(0o700)
        with self.assertRaises(FoundationError) as error:
            build(SENTENCE, self.candidate, self.root / 'unknown', fake, self.native)
        self.assertEqual(error.exception.outcome, 'Unknown')

    def test_timeout_is_not_promoted_to_success(self):
        fake = self.root / 'timeout-solver'
        fake.write_text('#!/usr/bin/env python3\nimport time\ntime.sleep(30)\n')
        fake.chmod(0o700)
        with self.assertRaises(FoundationError) as error:
            build(SENTENCE, self.candidate, self.root / 'timeout', fake, self.native, timeout_ms=1)
        self.assertEqual(error.exception.outcome, 'Timeout')

    def test_stronger_native_policy_remains_unsupported(self):
        with self.assertRaises(FoundationError) as error:
            build(SENTENCE, self.candidate, self.root / 'strict', self.solver, self.native, policy='strict_native_exact')
        self.assertEqual(error.exception.outcome, 'Unsupported')

    def test_hash_consistent_wrong_translation_is_actually_checked(self):
        directory = self.copy_capsule()
        source = (directory / 'generated.rs').read_text().replace(
            'else_branch:Box::new(Expr::Int(0i64))', 'else_branch:Box::new(Expr::Int(1i64))')
        target = decode(source)
        (directory / 'generated.rs').write_text(source)
        write_json(directory / 'translation-ir.json', target)
        query, _ = equivalence_query(load(directory / 'candidate-ir.json'), target)
        (directory / 'translation.smt2').write_text(query)
        self.rehash(directory, 'generated.rs', 'translation-ir.json', 'translation.smt2')
        evidence = self.manifest(directory)
        evidence['canonical_identities']['translation'] = identity('program-ir', target)
        write_json(directory / 'capsule.json', evidence)
        self.assert_invalid(directory)

    def cli(self, *args):
        result = subprocess.run([sys.executable, '-m', 'foundation', '--solver', self.solver,
                                 '--cargo', self.native.cargo, '--rustc', self.native.rustc, *args],
                                capture_output=True, text=True, timeout=30)
        return result.returncode, json.loads(result.stdout)

    def test_cli_run_executes_checked_artifact(self):
        code, result = self.cli('run', str(self.base), '--input', '{"x":"-1"}')
        self.assertEqual(code, 0)
        self.assertEqual(result['observation'], {'kind': 'return', 'type': 'i64', 'value': '0'})

    def test_cli_refutation_returns_typed_exit_and_replayed_witness(self):
        code, result = self.cli('build', '--request', 'examples/e2e/nonnegative/request.txt',
                                '--candidate', 'examples/e2e/nonnegative/wrong-branch.rz', '--out', str(self.root / 'cli-refuted'))
        self.assertEqual(code, 2)
        self.assertEqual(result['outcome'], 'Refuted')
        self.assertTrue(result['counterexample']['validated'])

    def test_cli_does_not_silently_accept_imprecise_input(self):
        code, result = self.cli('run', str(self.base), '--input', '{"x":9007199254740993}')
        self.assertEqual(code, 5)
        self.assertEqual(result['outcome'], 'InvalidEvidence')

    def test_cli_malformed_manifest_returns_typed_rejection(self):
        directory = self.copy_capsule()
        valid = self.manifest(directory)
        bad_hashes = copy.deepcopy(valid)
        bad_hashes['artifact_hashes'] = None
        for manifest in [None, [None], bad_hashes]:
            with self.subTest(manifest=manifest):
                write_json(directory / 'capsule.json', manifest)
                code, result = self.cli('check', str(directory))
                self.assertEqual(code, 5)
                self.assertEqual(result['outcome'], 'InvalidEvidence')


if __name__ == '__main__':
    unittest.main()
