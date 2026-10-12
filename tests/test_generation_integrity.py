"""Independent byte-identity conformance for deterministic generation provenance."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from foundation.ir import file_hash, load, write_json


@unittest.skipUnless(os.environ.get('FOUNDATION_E2E') == '1', 'Full solver/native gate')
class GenerationIntegrityTests(unittest.TestCase):
    def test_rehashed_line_endings_cannot_claim_exact_generated_bytes(self):
        with tempfile.TemporaryDirectory(prefix='foundation-generation-bytes-') as scratch:
            capsule = Path(scratch) / 'capsule'
            command = [sys.executable, '-m', 'foundation', '--solver',
                       os.environ.get('FOUNDATION_SOLVER', '/usr/bin/z3')]
            generated = subprocess.run(command + ['synthesize', '--request',
                                       'examples/e2e/nonnegative/request.txt', '--out', str(capsule)],
                                       capture_output=True, text=True, timeout=90)
            self.assertEqual(generated.returncode, 0, generated.stdout)
            source = capsule / 'candidate.rz'
            source.write_bytes(source.read_bytes().replace(b'\n', b'\r\n'))
            manifest = load(capsule / 'capsule.json')
            manifest['artifact_hashes']['candidate.rz'] = file_hash(source)
            manifest['generation']['candidate_source_sha256'] = file_hash(source)
            write_json(capsule / 'capsule.json', manifest)
            checked = subprocess.run(command + ['check', str(capsule)], capture_output=True,
                                     text=True, timeout=90)
            self.assertEqual(checked.returncode, 5, checked.stdout)
            result = json.loads(checked.stdout)
            self.assertEqual(result['outcome'], 'InvalidEvidence')
            self.assertEqual(result['stage'], 'generation')
