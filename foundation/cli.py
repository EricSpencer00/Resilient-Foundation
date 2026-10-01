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
    args = parser.parse_args()
    try:
        if args.command == 'intent':
            spec, ledger = interpret(args.request.read_text())
            result = {'spec': spec, 'ledger': ledger}
        elif args.command == 'source':
            model, source_map = parse_source(args.candidate.read_text())
            result = {'program': model, 'source_map': source_map}
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
