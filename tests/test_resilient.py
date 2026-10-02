"""Independent checks for the Resilient evidence boundary."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import copy
import sys

from foundation.errors import FoundationError
from foundation.resilient import ANCHORS, import_evidence, inspect, verify_evidence


class ResilientEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="foundation-resilient-test-")
        self.root = Path(self.scratch.name) / "resilient"
        for relative in ANCHORS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("anchor: " + relative + "\n")
        self.source = self.root / "candidate.rz"
        self.source.write_text("fn f(int x) -> int { return x; }\n")
        self.cert_dir = Path(self.scratch.name) / "certs"
        self.cert_dir.mkdir()
        self.smt = self.cert_dir / "f__requires__0.smt2"
        self.smt.write_text("(set-logic QF_LIA)\n(check-sat)\n")
        self.certificate = Path(self.scratch.name) / "certificate.json"
        self.certificate.write_text(json.dumps({
            "schema": "resilient-contract-certificate/v1",
            "schema_version": 1,
            "source": "candidate.rz",
            "functions": [{
                "name": "f",
                "enrolled": True,
                "provenance": [],
                "clauses": [{"clause": "x == x", "kind": "requires",
                             "smtlib2": "(check-sat)\n", "verdict": "pass"}],
            }],
        }))
        self.manifest = self.cert_dir / "manifest.json"
        self.manifest.write_text(json.dumps({
            "program": "candidate.rz",
            "obligations": [{
                "fn": "f", "kind": "requires", "idx": 0,
                "cert": self.smt.name,
                "sha256": hashlib.sha256(self.smt.read_bytes()).hexdigest(),
            }],
        }))

    def tearDown(self):
        self.scratch.cleanup()

    def test_inventory_binds_every_anchor_and_is_deterministic(self):
        first = inspect(self.root)
        second = inspect(self.root)
        self.assertEqual(first, second)
        self.assertEqual(set(first["anchors"]), set(ANCHORS))
        self.assertEqual(len(first["inventory_sha256"]), 64)

    def test_unsigned_certificate_import_is_explicitly_artifact_checked(self):
        evidence = import_evidence(self.root, self.source, self.certificate, self.cert_dir)
        self.assertEqual(evidence["evidence_class"], "artifact_checked")
        self.assertEqual(evidence["contract_certificate"]["verdicts"], {"pass": 1, "fail": 0, "unknown": 0})
        self.assertFalse(evidence["proof_directory"]["batch_signature_present"])

    def test_source_filename_binding_is_closed(self):
        self.certificate.write_text(self.certificate.read_text().replace("candidate.rz", "other.rz"))
        with self.assertRaises(FoundationError) as error:
            import_evidence(self.root, self.source, self.certificate, self.cert_dir)
        self.assertEqual(error.exception.outcome, "InvalidEvidence")

    def test_open_contract_verdict_is_not_promoted(self):
        certificate = json.loads(self.certificate.read_text())
        certificate["functions"][0]["clauses"][0] = {"clause": "x == x", "kind": "requires", "verdict": "unknown"}
        self.certificate.write_text(json.dumps(certificate))
        with self.assertRaises(FoundationError) as error:
            import_evidence(self.root, self.source, self.certificate, self.cert_dir)
        self.assertEqual(error.exception.outcome, "InvalidEvidence")

    def tool(self, name, body):
        path = Path(self.scratch.name) / name
        path.write_text('#!' + sys.executable + '\n' + body)
        path.chmod(0o700)
        return path

    def test_rz_success_cannot_stand_in_for_solver_replay(self):
        rz = self.tool('rz', "print('warning: Z3 unavailable; skipping replay')\n")
        z3 = self.tool('solver', "print('sat')\n")
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir, rz, z3)

    def test_z3_is_used_even_without_rz(self):
        z3 = self.tool('solver', "print('sat')\n")
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir, z3=z3)

    def test_contract_queries_are_replayed_as_well_as_manifest_queries(self):
        z3 = self.tool('solver', "import sys\nq = sys.stdin.read()\nprint('sat' if '(assert true)' in q else 'unsat')\n")
        certificate = json.loads(self.certificate.read_text())
        certificate['functions'][0]['clauses'][0]['smtlib2'] = '(assert true)\n(check-sat)\n'
        self.certificate.write_text(json.dumps(certificate))
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir, z3=z3)

    def test_solver_output_spoofing_command_is_rejected_before_execution(self):
        self.smt.write_text('(echo "unsat")\n(exit)\n')
        manifest = json.loads(self.manifest.read_text())
        manifest['obligations'][0]['sha256'] = hashlib.sha256(self.smt.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir)

    def test_record_metadata_cannot_be_forged_or_replay_downgraded(self):
        evidence = import_evidence(self.root, self.source, self.certificate, self.cert_dir)
        path = Path(self.scratch.name) / 'evidence.json'
        for field, value in [('evidence_class', 'kernel_checked'), ('integration_id', 'forged'),
                             ('verification', {'status': 'passed'}), ('limitations', [])]:
            with self.subTest(field=field):
                mutated = copy.deepcopy(evidence)
                mutated[field] = value
                path.write_text(json.dumps(mutated))
                with self.assertRaises(FoundationError):
                    verify_evidence(path, self.root, self.source, self.certificate, self.cert_dir)

    def test_reimported_stale_certificate_must_be_compared_with_current_source(self):
        # A producer that exits successfully but emits no fresh artifacts must
        # never establish a source binding, even if old queries replay.
        self.source.write_text('fn f(int x) -> int { return x + 1; }\n')
        rz = self.tool('rz', "print('all checks passed')\n")
        z3 = self.tool('solver', "print('unsat')\n")
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir, rz, z3)

    def test_empty_or_duplicate_manifest_does_not_create_solver_evidence(self):
        original = json.loads(self.manifest.read_text())
        for obligations in [[], original['obligations'] * 2]:
            with self.subTest(obligations=obligations):
                self.manifest.write_text(json.dumps({**original, 'obligations': obligations}))
                with self.assertRaises(FoundationError):
                    import_evidence(self.root, self.source, self.certificate, self.cert_dir)

    def test_malformed_verdict_and_boolean_version_return_typed_rejection(self):
        original = json.loads(self.certificate.read_text())
        for field in ['verdict', 'version']:
            mutated = copy.deepcopy(original)
            if field == 'verdict':
                mutated['functions'][0]['clauses'][0]['verdict'] = []
            else:
                mutated['schema_version'] = True
            self.certificate.write_text(json.dumps(mutated))
            with self.subTest(field=field), self.assertRaises(FoundationError):
                import_evidence(self.root, self.source, self.certificate, self.cert_dir)

    def test_symlinked_source_is_rejected(self):
        alias = Path(self.scratch.name) / 'candidate.rz'
        alias.symlink_to(self.source)
        with self.assertRaises(FoundationError):
            import_evidence(self.root, alias, self.certificate, self.cert_dir)

    def producer(self):
        # A test double for orchestration only. Real source/solver acceptance
        # uses the separately built rz and Z3 in the integration runner.
        certificate = json.loads(self.certificate.read_text())
        manifest = json.loads(self.manifest.read_text())
        return self.tool('rz', f'''import json, sys
from pathlib import Path
args = sys.argv
source = Path(args[-1])
certificate = {certificate!r}
certificate['source'] = str(source)
if 'return x + 1' in source.read_text():
    certificate['functions'][0]['clauses'][0]['clause'] = 'changed clause'
Path(args[args.index('--emit-contract-certificate') + 1]).write_text(json.dumps(certificate))
proofs = Path(args[args.index('--emit-certificate') + 1])
proofs.mkdir()
manifest = {manifest!r}
manifest['program'] = str(source)
(proofs / 'manifest.json').write_text(json.dumps(manifest))
(proofs / {self.smt.name!r}).write_bytes({self.smt.read_bytes()!r})
''')

    def test_regeneration_replay_receipt_and_stale_reimport(self):
        rz = self.producer()
        z3 = self.tool('chosen-solver', "print('unsat')\n")
        path = Path(self.scratch.name) / 'evidence.json'
        evidence = import_evidence(self.root, self.source, self.certificate, self.cert_dir, rz, z3, path)
        self.assertEqual(evidence['source_binding']['status'], 'regenerated')
        self.assertEqual(evidence['verification']['solver']['name'], 'chosen-solver')
        self.assertEqual(len(evidence['verification']['queries']), 2)
        self.assertEqual(evidence['claim_scope'], 'smt_queries')
        verify_evidence(path, self.root, self.source, self.certificate, self.cert_dir, rz, z3)
        with self.assertRaises(FoundationError):
            verify_evidence(path, self.root, self.source, self.certificate, self.cert_dir)
        self.source.write_text('fn f(int x) -> int { return x + 1; }\n')
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir, rz, z3)

    def test_regeneration_rejects_program_actions_before_invoking_compiler(self):
        for text in ['fn f(int x) -> int { return x; } f(1);',
                     'fn f(int x) -> int { return system(x); }',
                     'use "other.rz"; fn f(int x) -> int { return x; }']:
            self.source.write_text(text)
            with self.subTest(text=text), self.assertRaises(FoundationError) as error:
                import_evidence(self.root, self.source, self.certificate, self.cert_dir, self.producer())
            self.assertEqual(error.exception.outcome, 'Unsupported')

    def test_compiler_only_clauses_are_not_promoted_to_solver_claims(self):
        certificate = json.loads(self.certificate.read_text())
        certificate['functions'][0]['clauses'].append(
            {'clause': 'result == x', 'kind': 'ensures', 'verdict': 'pass', 'basis': 'implementation'})
        self.certificate.write_text(json.dumps(certificate))
        z3 = self.tool('solver', "print('unsat')\n")
        evidence = import_evidence(self.root, self.source, self.certificate, self.cert_dir, z3=z3)
        self.assertEqual(evidence['source_binding']['status'], 'associated_only')
        self.assertEqual(evidence['contract_certificate']['compiler_reported_only'], ['contract:f:1:ensures'])
        self.assertEqual(len(evidence['verification']['queries']), 2)

    def test_solver_faults_remain_distinct_and_fail_closed(self):
        for output, outcome in [('sat', 'Refuted'), ('unknown', 'Unknown'),
                                ('unsat\\nsat', 'InvalidEvidence'), ('', 'InvalidEvidence')]:
            solver = self.tool('solver', f'print({output!r})\n')
            with self.subTest(output=output), self.assertRaises(FoundationError) as error:
                import_evidence(self.root, self.source, self.certificate, self.cert_dir, z3=solver)
            self.assertEqual(error.exception.outcome, outcome)

    def test_signature_bytes_are_bound_without_authentication_claim(self):
        signature = self.cert_dir / 'cert.sig'
        signature.write_text('ab' * 64)
        evidence = import_evidence(self.root, self.source, self.certificate, self.cert_dir)
        self.assertEqual(evidence['proof_directory']['authentication'], 'not_checked')
        self.assertEqual(evidence['proof_directory']['batch_signature_sha256'],
                         hashlib.sha256(signature.read_bytes()).hexdigest())
        signature.write_text('invalid')
        with self.assertRaises(FoundationError):
            import_evidence(self.root, self.source, self.certificate, self.cert_dir)


if __name__ == "__main__":
    unittest.main()
