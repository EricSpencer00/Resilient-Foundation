"""Configured native tools must apply consistently to public CLI subprocesses."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('FOUNDATION_E2E') == '1', 'Full solver/native gate')
class CliToolchainTests(unittest.TestCase):
    def test_configured_native_tool_is_not_silently_replaced_by_path_tool(self):
        for variable in ['FOUNDATION_CARGO', 'FOUNDATION_RUSTC']:
            with self.subTest(variable=variable), tempfile.TemporaryDirectory(prefix='foundation-tool-selection-') as scratch:
                root = Path(scratch)
                sentinel = 'configured-' + variable.lower()
                tool = root / 'rejecting-tool'
                tool.write_text('#!/bin/sh\necho ' + sentinel + ' >&2\nexit 7\n')
                tool.chmod(0o755)
                environment = dict(os.environ, **{variable: str(tool)})
                result = subprocess.run([sys.executable, '-m', 'foundation', 'synthesize', '--request',
                                         'examples/e2e/nonnegative/request.txt', '--out', str(root / 'capsule')],
                                        env=environment, capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 1, result.stdout)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt['stage'], 'native')
                self.assertIn(sentinel, receipt['reason'])
                self.assertFalse((root / 'capsule/capsule.json').exists())
