"""Public CLI conformance for accepted-intent synthesis and evidence replay."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from foundation.ir import file_hash, load, write_json


@unittest.skipUnless(os.environ.get('FOUNDATION_E2E') == '1', 'Full solver/native gate')
class SynthesisE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix='foundation-synthesis-')
        cls.root = Path(cls.scratch.name)
        cls.request = Path('examples/e2e/nonnegative/request.txt')
        cls.capsule = cls.root / 'accepted'
        cls.solver = os.environ.get('FOUNDATION_SOLVER', '/usr/bin/z3')
        code, cls.receipt = cls.cli('synthesize', '--request', str(cls.request), '--out', str(cls.capsule))
        if code:
            raise AssertionError(cls.receipt)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    @classmethod
    def cli(cls, *args):
        command = [sys.executable, '-m', 'foundation', '--solver', cls.solver, *args]
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        return result.returncode, json.loads(result.stdout)

    def test_accepted_intent_synthesizes_checked_executable(self):
        self.assertEqual(self.receipt['outcome'], 'Proved')
        manifest = load(self.capsule / 'capsule.json')
        self.assertEqual(manifest['intent']['status'], 'accepted')
        self.assertEqual(manifest['generation']['role'], 'deterministic_spec_ir_v1')
        self.assertEqual(manifest['formal']['evidence_class'], 'solver_checked')
        self.assertEqual(manifest['translation']['evidence_class'], 'translation_checked')
        self.assertEqual(manifest['native']['relation'], 'trusted_compilation')
        for value, expected in [('-9223372036854775808', '0'), ('0', '0'), ('9223372036854775807', '9223372036854775807')]:
            with self.subTest(value=value):
                code, result = self.cli('run', str(self.capsule), '--input', json.dumps({'x': value}))
                self.assertEqual(code, 0, result)
                self.assertEqual(result['observation'], {'kind': 'return', 'type': 'i64', 'value': expected})

    def test_ambiguous_intent_has_explicit_decision_obligation_and_no_capsule(self):
        request = self.root / 'ambiguous.txt'
        request.write_text('For an integer x, return x if x is nonnegative, and return one otherwise.\n')
        output = self.root / 'ambiguous'
        code, result = self.cli('synthesize', '--request', str(request), '--out', str(output))
        self.assertEqual(code, 6, result)
        self.assertEqual(result['outcome'], 'NeedsDecision')
        self.assertTrue(result['obligations'])
        self.assertEqual(result['obligations'][0]['id'], 'accept-formal-intent')
        self.assertFalse(output.exists())

    def test_rehashed_equivalent_source_cannot_impersonate_synthesized_source(self):
        changed = self.root / 'changed'
        shutil.copytree(self.capsule, changed)
        source = changed / 'candidate.rz'
        source.write_text(source.read_text() + '\n')
        manifest = load(changed / 'capsule.json')
        manifest['artifact_hashes']['candidate.rz'] = file_hash(source)
        manifest['generation']['candidate_source_sha256'] = file_hash(source)
        write_json(changed / 'capsule.json', manifest)
        code, result = self.cli('check', str(changed))
        self.assertEqual(code, 5, result)
        self.assertEqual(result['outcome'], 'InvalidEvidence')


if __name__ == '__main__':
    unittest.main()
