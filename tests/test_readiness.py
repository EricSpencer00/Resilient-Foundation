"""Readiness must never mutate GitHub after a failed local or identity gate."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReadinessTests(unittest.TestCase):
    def invoke(self, failure='', *, clean=True, matching=True):
        with tempfile.TemporaryDirectory(prefix='foundation-ready-test-') as scratch:
            root = Path(scratch)
            log = root / 'calls'
            mock = root / 'mock'
            mock.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['READY_TEST_LOG'], 'a') as output:
    output.write(name + ' ' + ' '.join(args) + '\\n')
if name == 'git':
    if args[:2] == ['status', '--porcelain']:
        print(' M foundation/cli.py' if os.environ['READY_TEST_CLEAN'] == '0' else '', end='')
    elif args[:2] == ['rev-parse', '--show-toplevel']:
        print(os.environ['READY_TEST_ROOT'])
    elif args[:1] == ['rev-parse']:
        print('abc123')
    elif 'diff' in args:
        print('A\\tfoundation/new.py\\nA\\ttests/test_new.py')
if name == 'gh':
    if args[:2] == ['repo', 'view']:
        print('EricSpencer00/Resilient-Foundation')
    elif args[:2] == ['pr', 'view']:
        print(('abc123' if os.environ['READY_TEST_MATCHING'] == '1' else 'wrong') + '\tmain\tOPEN')
if os.environ['READY_TEST_FAILURE'] and os.environ['READY_TEST_FAILURE'] in name + ' ' + ' '.join(args):
    sys.exit(1)
''')
            mock.chmod(0o755)
            for tool in ['git', 'gh', 'make', 'cargo', 'python3']:
                # The mock uses an absolute interpreter to avoid recursive PATH dispatch.
                (root / tool).symlink_to(mock)
            mock.write_text(mock.read_text().replace('#!/usr/bin/env python3', '#!' + os.sys.executable, 1))
            environment = dict(os.environ, PATH=str(root) + ':' + os.environ['PATH'],
                               READY_TEST_ROOT=str(ROOT), READY_TEST_LOG=str(log),
                               READY_TEST_FAILURE=failure, READY_TEST_CLEAN=str(int(clean)),
                               READY_TEST_MATCHING=str(int(matching)))
            result = subprocess.run(['bash', str(ROOT / 'agent-scripts/ready-or-bail.sh'), '--pr', '5'],
                                    env=environment, capture_output=True, text=True, timeout=10)
            return result, log.read_text() if log.exists() else ''

    def test_failed_required_gates_never_mark_ready(self):
        for failure in ['make check', 'cargo build', 'scripts/run_e2e.py', 'scripts/replay_resilient.py',
                        'scripts/validate_spec.py']:
            with self.subTest(failure=failure):
                result, calls = self.invoke(failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('gh pr ready', calls)
                self.assertNotIn('gh pr edit', calls)

    def test_dirty_or_wrong_remote_head_never_mark_ready(self):
        for options in [{'clean': False}, {'matching': False}]:
            with self.subTest(options=options):
                result, calls = self.invoke(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('gh pr ready', calls)

    def test_success_runs_all_gates_before_ready(self):
        result, calls = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        for gate in ['make check', 'cargo build', 'scripts/run_e2e.py', 'scripts/replay_resilient.py',
                     'scripts/validate_spec.py']:
            self.assertLess(calls.index(gate), calls.index('gh pr ready'))
