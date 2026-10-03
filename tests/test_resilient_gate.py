"""CLI gates must fail before compiler use when the pinned checkout differs."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PinnedGateTests(unittest.TestCase):
    def test_mismatched_revision_fails_before_output_or_compiler_invocation(self):
        with tempfile.TemporaryDirectory() as scratch:
            checkout = ROOT
            output = Path(scratch) / 'out'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_resilient_integration.py'),
                                     '--resilient-root', str(checkout), '--out', str(output),
                                     '--expected-revision', '0' * 40, '--rz', '/no/such/compiler'],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Pinned Resilient revision differs', result.stderr)
            self.assertFalse(output.exists())
