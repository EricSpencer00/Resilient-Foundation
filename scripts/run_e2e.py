#!/usr/bin/env python3
"""Run the actual scalar gate and retain a source-bound, host-specific report."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
import time
import unittest
from importlib.metadata import version
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from foundation.errors import FoundationError
from foundation.ir import file_hash, load, require, write_json
from foundation.native import NativeTools
from foundation.pipeline import build, implementation_identity, run, solver_identity
from foundation import smt

ORACLE_HASH = '353683fa08bc2e60c2fd5eeea2e0ce5a17572892bdfff7c621595941f9de640e'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT / 'validation/e2e.json')
    parser.add_argument('--evidence-dir', type=Path, default=ROOT / 'validation/e2e')
    parser.add_argument('--solver', default=shutil.which('z3') or '/usr/bin/z3')
    args = parser.parse_args()
    os.chdir(ROOT)
    os.environ['FOUNDATION_E2E'] = '1'
    os.environ['FOUNDATION_SOLVER'] = args.solver
    native = NativeTools(os.environ.get('FOUNDATION_CARGO'), os.environ.get('FOUNDATION_RUSTC'))
    require(file_hash(ROOT / 'examples/nonnegative/oracle.json') == ORACLE_HASH, 'Frozen oracle was changed')
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    calls = {'in_process_real_solver_calls': 0, 'in_process_fault_solver_calls': 0,
             'in_process_native_compilations': 0, 'cli_subprocess_calls_excluded': True}
    actual_invoke, actual_compile = smt.invoke, NativeTools.compile
    trusted_solver = Path(args.solver).resolve()
    def counted_solver(solver, query, timeout_ms):
        key = 'in_process_real_solver_calls' if Path(solver).resolve() == trusted_solver else 'in_process_fault_solver_calls'
        calls[key] += 1
        return actual_invoke(solver, query, timeout_ms)
    def counted_compile(instance, directory, output='native'):
        result = actual_compile(instance, directory, output)
        calls['in_process_native_compilations'] += 1
        return result
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    with patch('foundation.smt.invoke', side_effect=counted_solver), patch.object(NativeTools, 'compile', counted_compile):
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        require(result.wasSuccessful() and not result.skipped, 'Required end-to-end gate failed or skipped', 'Error', 'e2e')
        with tempfile.TemporaryDirectory(prefix='foundation-recorded-e2e-') as scratch:
            capsule = Path(scratch) / 'accepted'
            request = (ROOT / 'examples/e2e/nonnegative/request.txt').read_text()
            candidate = (ROOT / 'examples/e2e/nonnegative/candidate.rz').read_text()
            receipt = build(request, candidate, capsule, args.solver, native)
            executions = []
            for case in load(ROOT / 'examples/nonnegative/oracle.json')['expected_cases']:
                observation = run(capsule, {'x': case['input']}, args.solver, native)
                require(observation['observation']['value'] == case['output'], 'Frozen oracle observation differs', 'Error', 'e2e')
                executions.append({'case_id': case['id'], **observation})
            for name in ['capsule.json', 'check-receipt.json', 'formal.smt2', 'translation.smt2',
                         'requirements.json', 'spec-ir.json', 'candidate-ir.json', 'source-map.json',
                         'generated.rs', 'translation-ir.json', 'candidate.rz', 'request.txt', 'profile.json']:
                shutil.copyfile(capsule / name, args.evidence_dir / name)
            write_json(args.evidence_dir / 'executions.json', {'cases': executions})
            try:
                build(request, (ROOT / 'examples/e2e/nonnegative/wrong-branch.rz').read_text(),
                      Path(scratch) / 'refuted', args.solver, native)
                raise FoundationError('Error', 'Wrong candidate was accepted', 'e2e')
            except FoundationError as exc:
                require(exc.outcome == 'Refuted', 'Wrong candidate failed for an unrelated reason', 'Error', 'e2e')
                write_json(args.evidence_dir / 'counterexample.json', exc.details['counterexample'])
    report = {
        'status': 'passed', 'scope': 'scalar_e2e_conformance', 'policy': receipt['policy'],
        'started_at_utc': started_at, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'host': platform.node(), 'architecture': platform.machine(), 'python': platform.python_version(),
        'python_dependencies': {'jsonschema': version('jsonschema')},
        'solver': solver_identity(args.solver), 'native_toolchain': native.identity(),
        'tests_run': result.testsRun, 'tests_failed': len(result.failures) + len(result.errors),
        'tests_skipped': len(result.skipped), 'oracle_cases_executed': len(executions),
        'elapsed_ms': int((time.monotonic() - started) * 1000), 'instrumented_operations': calls,
        'oracle_sha256': ORACLE_HASH, 'implementation_hashes': implementation_identity(),
        'test_hashes': {str(p.relative_to(ROOT)): file_hash(p) for p in sorted((ROOT / 'tests').glob('test_*.py'))},
        'driver_hashes': {'scripts/run_e2e.py': file_hash(ROOT / 'scripts/run_e2e.py')},
        'evidence_files': {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(args.evidence_dir.iterdir()) if p.is_file()},
        'capability_ids': ['scalar-smt', 'translation-ir'], 'formal_class': 'solver_checked',
        'translation_class': 'translation_checked', 'native_relation': 'trusted_compilation',
        'model_generation': 'interactive Codex-authored candidate; no attested snapshot or model benchmark',
        'limitations': ['No kernel-checked UNSAT proof or native machine-code equivalence.',
                        'Native source runs the reference evaluator; it is not direct optimized code generation.',
                        'Recorded native executable is not included in the evidence directory; rebuild the capsule to execute.',
                        'Absolute build paths and host toolchains bind native evidence; records are host-specific.'],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.report, report)
    print(json.dumps({k: report[k] for k in ['status', 'scope', 'host', 'tests_run', 'tests_failed', 'tests_skipped', 'oracle_cases_executed', 'instrumented_operations']}, indent=2))


if __name__ == '__main__':
    main()
