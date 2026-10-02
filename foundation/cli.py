import argparse
import json
from pathlib import Path
import shutil
import sys

from .errors import EXIT_CODES, FoundationError
from .intent import interpret
from .ir import loads
from .native import NativeTools
from .pipeline import POLICY, build, check, run
from .resilient import import_evidence, inspect as inspect_resilient, verify_evidence
from .source import parse_source


def main():
    parser = argparse.ArgumentParser(prog='foundation', description='Checked scalar workflow with explicit trusted Rust compilation')
    parser.add_argument('--solver', default=shutil.which('z3') or '/usr/bin/z3')
    parser.add_argument('--cargo', default=shutil.which('cargo'))
    parser.add_argument('--rustc', default=shutil.which('rustc'))
    commands = parser.add_subparsers(dest='command', required=True)
    intent = commands.add_parser('intent')
    intent.add_argument('request', type=Path)
    source = commands.add_parser('source')
    source.add_argument('candidate', type=Path)
    create = commands.add_parser('build')
    create.add_argument('--request', required=True, type=Path)
    create.add_argument('--candidate', required=True, type=Path)
    create.add_argument('--out', required=True, type=Path)
    create.add_argument('--policy', default=POLICY)
    create.add_argument('--timeout-ms', type=int, default=10000)
    verify = commands.add_parser('check')
    verify.add_argument('capsule', type=Path)
    verify.add_argument('--policy', default=POLICY)
    execute = commands.add_parser('run')
    execute.add_argument('capsule', type=Path)
    execute.add_argument('--input', required=True, help='JSON object; i64 values are decimal strings')
    execute.add_argument('--policy', default=POLICY)
    resilient = commands.add_parser('resilient', help='inventory and verify an existing Resilient checkout')
    resilient_commands = resilient.add_subparsers(dest='resilient_command', required=True)
    resilient_inspect = resilient_commands.add_parser('inspect')
    resilient_inspect.add_argument('--root', required=True, type=Path)
    resilient_import = resilient_commands.add_parser('import-cert')
    resilient_import.add_argument('--root', required=True, type=Path)
    resilient_import.add_argument('--source', required=True, type=Path)
    resilient_import.add_argument('--certificate', required=True, type=Path)
    resilient_import.add_argument('--certificate-dir', required=True, type=Path)
    resilient_import.add_argument('--rz', type=Path)
    resilient_import.add_argument('--z3', type=Path)
    resilient_import.add_argument('--out', type=Path)
    resilient_verify = resilient_commands.add_parser('verify-evidence')
    resilient_verify.add_argument('--evidence', required=True, type=Path)
    resilient_verify.add_argument('--root', required=True, type=Path)
    resilient_verify.add_argument('--source', required=True, type=Path)
    resilient_verify.add_argument('--certificate', required=True, type=Path)
    resilient_verify.add_argument('--certificate-dir', required=True, type=Path)
    resilient_verify.add_argument('--rz', type=Path)
    resilient_verify.add_argument('--z3', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'intent':
            spec, ledger = interpret(args.request.read_text())
            result = {'spec': spec, 'ledger': ledger}
        elif args.command == 'source':
            model, source_map = parse_source(args.candidate.read_text())
            result = {'program': model, 'source_map': source_map}
        elif args.command == 'resilient':
            if args.resilient_command == 'inspect':
                result = inspect_resilient(args.root)
            elif args.resilient_command == 'import-cert':
                result = import_evidence(args.root, args.source, args.certificate,
                                         args.certificate_dir, args.rz, args.z3, args.out)
            else:
                result = verify_evidence(args.evidence, args.root, args.source, args.certificate,
                                         args.certificate_dir, args.rz, args.z3)
        else:
            native = NativeTools(args.cargo, args.rustc)
            if args.command == 'build':
                result = build(args.request.read_text(), args.candidate.read_text(), args.out, args.solver,
                               native, args.policy, args.timeout_ms)
            elif args.command == 'check':
                result, _ = check(args.capsule, args.solver, native, args.policy)
            else:
                result = run(args.capsule, loads(args.input), args.solver, native, args.policy)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except FoundationError as exc:
        print(json.dumps(exc.as_dict(), indent=2, allow_nan=False))
        return EXIT_CODES.get(exc.outcome, 1)
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps({'outcome': 'Error', 'stage': 'operation', 'reason': str(exc)}, indent=2))
        return 1


if __name__ == '__main__':
    sys.exit(main())
