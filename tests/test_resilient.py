"""Independent checks for the Resilient evidence boundary."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from foundation.errors import FoundationError
from foundation.resilient import ANCHORS, import_evidence, inspect


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


if __name__ == "__main__":
    unittest.main()
