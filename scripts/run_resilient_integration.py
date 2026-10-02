#!/usr/bin/env python3
"""Regenerate and independently replay Resilient evidence on a compute host."""
import argparse
import copy
import json
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundation.errors import FoundationError
from foundation.ir import file_hash, write_json
from foundation.resilient import import_evidence, inspect, verify_evidence

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, timeout=900, env=None):
    started = time.monotonic()
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"command failed to run: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(f"command exited {result.returncode}: {command}\n{result.stderr[-4000:]}")
    return {"command": [str(item) for item in command], "seconds": round(time.monotonic() - started, 3),
            "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]}


def absolute(path):
    # Keep a rustup shim's basename; resolving cargo -> rustup breaks dispatch.
    return Path(os.path.abspath(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resilient-root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--cargo', default=os.environ.get('FOUNDATION_CARGO') or shutil.which('cargo'))
    parser.add_argument('--rustc', default=os.environ.get('FOUNDATION_RUSTC') or shutil.which('rustc'))
    parser.add_argument('--z3', default=os.environ.get('FOUNDATION_Z3') or shutil.which('z3'), type=Path)
    parser.add_argument('--rz', type=Path, help='Use an existing trusted binary; skip the build')
    parser.add_argument('--timeout', default=900, type=int)
    args = parser.parse_args()
    root = absolute(args.resilient_root)
    out = absolute(args.out)
    if out.exists() or out.is_symlink():
        raise RuntimeError('Output already exists; use a fresh path: ' + str(out))
    if not args.z3:
        raise RuntimeError('Z3 is required for the integration gate')
    z3 = absolute(args.z3)
    inventory = inspect(root)
    out.mkdir(parents=True)
    if args.rz:
        rz = absolute(args.rz)
        build = {'status': 'prebuilt', 'binary_sha256': file_hash(rz),
                 'assumption': 'Caller-selected trusted binary; build provenance is not independently proved.'}
    else:
        if not args.cargo or not args.rustc:
            raise RuntimeError('cargo and rustc are required when --rz is absent')
        cargo, rustc = absolute(args.cargo), absolute(args.rustc)
        env = dict(os.environ, RUSTC=str(rustc))
        build = {'status': 'built', **run([str(cargo), 'build', '--manifest-path',
                  str(root / 'resilient/Cargo.toml'), '--release', '--locked', '--features', 'z3'],
                  timeout=args.timeout, env=env)}
        rz = root / 'target/release/rz'
        build['binary_sha256'] = file_hash(rz)
    fixture = ROOT / 'examples/resilient/cert_demo_pass.rz'
    source = out / 'source' / fixture.name
    source.parent.mkdir()
    shutil.copyfile(fixture, source)
    certificate, cert_dir, evidence_path = out / 'contract-certificate.json', out / 'proofs', out / 'evidence.json'
    emit = run([str(rz), '--no-cache', '--typecheck', '--emit-contract-certificate', str(certificate),
                '--emit-certificate', str(cert_dir), str(source)], timeout=args.timeout)
    evidence = import_evidence(root, source, certificate, cert_dir, rz, z3, evidence_path)
    receipt = verify_evidence(evidence_path, root, source, certificate, cert_dir, rz, z3)
    if receipt['source_binding'] != 'regenerated' or receipt['evidence_class'] != 'solver_checked':
        raise RuntimeError('Required source regeneration or direct solver replay did not pass')

    cases = [{'id': 'regenerate-and-replay', 'status': 'passed'},
             {'id': 'verify-complete-record', 'status': 'passed'}]
    def rejects(name, action, expected=None):
        try:
            action()
        except FoundationError as error:
            if expected and error.outcome != expected:
                raise RuntimeError(f'{name}: expected {expected}, got {error.outcome}') from error
            cases.append({'id': name, 'status': 'passed', 'outcome': error.outcome})
        else:
            raise RuntimeError(name + ': invalid evidence was accepted')
    original_source = source.read_bytes()
    source.write_bytes(original_source + b'\n// stale identity\n')
    rejects('source-identity-mutation', lambda: verify_evidence(evidence_path, root, source, certificate, cert_dir, rz, z3))
    source.write_bytes(original_source.replace(b'return x;', b'return x + 1;'))
    rejects('stale-certificate-reimport', lambda: import_evidence(root, source, certificate, cert_dir, rz, z3))
    source.write_bytes(original_source)
    forged = copy.deepcopy(evidence)
    forged['evidence_class'] = 'kernel_checked'
    write_json(evidence_path, forged)
    rejects('forged-assurance', lambda: verify_evidence(evidence_path, root, source, certificate, cert_dir, rz, z3))
    write_json(evidence_path, evidence)
    rejects('replay-downgrade', lambda: verify_evidence(evidence_path, root, source, certificate, cert_dir))
    proof = cert_dir / evidence['proof_directory']['obligations'][0]['certificate']
    original_proof, original_manifest = proof.read_bytes(), (cert_dir / 'manifest.json').read_bytes()
    manifest = json.loads(original_manifest)
    proof.write_text('(assert true)\n(check-sat)\n')
    manifest['obligations'][0]['sha256'] = file_hash(proof)
    write_json(cert_dir / 'manifest.json', manifest)
    rejects('satisfiable-query', lambda: import_evidence(root, source, certificate, cert_dir, z3=z3), 'Refuted')
    proof.write_text('(echo "unsat")\n(exit)\n')
    manifest['obligations'][0]['sha256'] = file_hash(proof)
    write_json(cert_dir / 'manifest.json', manifest)
    rejects('solver-output-spoofing', lambda: import_evidence(root, source, certificate, cert_dir, z3=z3), 'InvalidEvidence')
    proof.write_bytes(original_proof)
    (cert_dir / 'manifest.json').write_bytes(original_manifest)

    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_resilient.py')
    results = unittest.TextTestRunner(verbosity=1).run(suite)
    if not results.wasSuccessful() or results.skipped:
        raise RuntimeError('Independent boundary regression suite failed or skipped')
    implementation_paths = [
        'foundation/resilient.py', 'foundation/source.py', 'foundation/cli.py', 'foundation/errors.py', 'foundation/ir.py',
        'profiles/scalar-wrapping-v1.json', 'schemas/program-ir.schema.json',
        'profiles/resilient-capabilities.json', 'schemas/resilient-capabilities.schema.json',
        'schemas/resilient-integration-report.schema.json', 'profiles/backend-capabilities.json',
        'scripts/validate_spec.py', 'examples/resilient/cert_demo_pass.rz',
    ]
    def hashes(paths):
        return {path: file_hash(ROOT / path) for path in paths}
    evidence_files = {'validation/resilient/' + path.relative_to(out).as_posix(): file_hash(path)
                      for path in sorted(out.rglob('*')) if path.is_file()}
    report = {
        'version': '0.1.0-draft', 'kind': 'resilient_integration_report',
        'format': 'foundation-resilient-integration-report-v2', 'status': 'passed',
        'scope': 'resilient_contract_certificate_e2e', 'evidence_class': 'solver_checked',
        'claim_scope': 'smt_queries', 'source_binding': 'regenerated',
        'capability_ids': ['source-frontend', 'contract-verification', 'proof-certificates'],
        'inventoried_capability_ids': inventory['capability_ids'],
        'inventory_sha256': inventory['inventory_sha256'], 'source_sha256': file_hash(source),
        'certificate_sha256': file_hash(certificate),
        'proof_manifest_sha256': evidence['proof_directory']['manifest_sha256'],
        'build': build, 'emit': emit, 'replay': evidence['verification'], 'receipt': receipt, 'cases': cases,
        'mutation': {'status': 'rejected'}, 'implementation_hashes': hashes(implementation_paths),
        'test_hashes': hashes(['tests/test_resilient.py']),
        'driver_hashes': hashes(['scripts/run_resilient_integration.py', 'scripts/replay_resilient.py']),
        'evidence_files': evidence_files, 'tests_run': results.testsRun + len(cases),
        'tests_failed': 0, 'tests_skipped': 0, 'assumptions': evidence['limitations'],
    }
    write_json(out / 'report.json', report)
    print(json.dumps({'status': 'passed', 'report': str(out / 'report.json'),
                      'tests_run': report['tests_run'], 'queries_replayed': len(evidence['verification']['queries'])}))


if __name__ == '__main__':
    try:
        main()
    except (FoundationError, RuntimeError, OSError, ValueError) as error:
        print(json.dumps({'status': 'failed', 'reason': str(error)}), file=sys.stderr)
        raise SystemExit(1)
