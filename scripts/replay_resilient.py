#!/usr/bin/env python3
"""Replay the saved real Resilient SMT queries without rebuilding its compiler.

Checks source/query identities and record claims. This gate does not rerun
source regeneration, authenticate signatures or validate the compiler encoding.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundation.resilient import _parse_contract_certificate, _parse_manifest, _query, _replay, _strict_json
from foundation.ir import file_hash
from foundation.errors import FoundationError


def replay(directory, z3):
    evidence = _strict_json(directory / 'evidence.json')
    source = directory / 'source' / evidence['source']['name']
    certificate = directory / 'contract-certificate.json'
    proofs = directory / 'proofs'
    parsed, counts = _parse_contract_certificate(certificate, source)
    manifest, records = _parse_manifest(proofs, source)
    if (evidence['format'] != 'foundation-resilient-evidence-v2' or
        evidence['evidence_class'] != 'solver_checked' or evidence['claim_scope'] != 'smt_queries' or
        evidence['source_binding']['status'] != 'regenerated' or counts['fail'] or counts['unknown'] or
        evidence['source']['sha256'] != file_hash(source) or
        evidence['contract_certificate']['sha256'] != file_hash(certificate) or
        evidence['proof_directory']['manifest_sha256'] != file_hash(proofs / 'manifest.json') or
        evidence['proof_directory']['obligations'] != records):
        raise FoundationError('InvalidEvidence', 'Saved Resilient artifact identity differs', 'evidence')
    queries = [{'id': f"contract:{f['name']}:{i}:{c['kind']}", 'text': _query(c['smtlib2'])}
               for f in parsed['functions'] for i, c in enumerate(f['clauses']) if 'smtlib2' in c]
    queries += [{'id': 'manifest:' + p['certificate'], 'text': _query((proofs / p['certificate']).read_text())}
                for p in records]
    result = _replay(queries, z3)
    if result['queries'] != evidence['verification']['queries']:
        raise FoundationError('InvalidEvidence', 'Saved Resilient query identities differ', 'evidence')
    return {'status': 'passed', 'scope': 'saved_smt_queries', 'queries_replayed': len(queries),
            'solver': result['solver']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('validation/resilient'))
    parser.add_argument('--z3', type=Path, default=Path('/usr/bin/z3'))
    args = parser.parse_args()
    try:
        print(json.dumps(replay(args.directory, args.z3)))
    except (FoundationError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'failed', 'reason': str(error)}), file=sys.stderr)
        raise SystemExit(1)
