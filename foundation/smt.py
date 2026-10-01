"""Error-observing, all-input QF_BV equivalence. Encoding and Z3 are trusted."""
from pathlib import Path
import re
import subprocess

from .errors import FoundationError
from .ir import binary, require, validate_program

SMT_OP = {
    'add_wrap': 'bvadd', 'sub_wrap': 'bvsub', 'mul_wrap': 'bvmul', 'div_wrap': 'bvsdiv',
    'eq': '=', 'lt_signed': 'bvslt', 'le_signed': 'bvsle',
    'gt_signed': 'bvsgt', 'ge_signed': 'bvsge', 'and': 'and', 'or': 'or',
}


class Encoder:
    def __init__(self, prefix, params):
        self.prefix, self.params, self.lines, self.count = prefix, params, [], 0

    def expr(self, expression):
        kind = expression['kind']
        if kind == 'int':
            value, error = '(_ bv' + str(int(expression['value']) % (1 << 64)) + ' 64)', 'false'
        elif kind == 'bool':
            value, error = str(expression['value']).lower(), 'false'
        elif kind == 'var':
            value, error = self.params[expression['name']], 'false'
        elif kind == 'if':
            cv, ce = self.expr(expression['condition'])
            yv, ye = self.expr(expression['then'])
            nv, ne = self.expr(expression['else'])
            value = f'(ite {cv} {yv} {nv})'
            error = f'(or {ce} (ite {cv} {ye} {ne}))'
        else:
            lv, le = self.expr(expression['left'])
            rv, re = self.expr(expression['right'])
            op = expression['op']
            value = f'({SMT_OP[op]} {lv} {rv})'
            if op == 'and':
                error = f'(or {le} (and {lv} {re}))'
            elif op == 'or':
                error = f'(or {le} (and (not {lv}) {re}))'
            elif op == 'div_wrap':
                error = f'(or {le} {re} (= {rv} (_ bv0 64)))'
            else:
                error = f'(or {le} {re})'
        number = self.count
        self.count += 1
        vname, ename = f'{self.prefix}{number}v', f'{self.prefix}{number}e'
        sort = 'Bool' if expression['type'] == 'bool' else '(_ BitVec 64)'
        self.lines.extend([f'(define-fun {vname} () {sort} {value})',
                           f'(define-fun {ename} () Bool {error})'])
        return vname, ename


def equivalence_query(spec, candidate, timeout_ms=10000):
    validate_program(spec)
    validate_program(candidate)
    left, right = spec['function'], candidate['function']
    require([p['type'] for p in left['params']] == [p['type'] for p in right['params']]
            and left['return_type'] == right['return_type'], 'Signatures differ', 'Unsupported', 'formal')
    require(1 <= timeout_ms <= 60000, 'Invalid solver timeout')
    lines = ['(set-logic QF_BV)', '(set-option :produce-models true)', f'(set-option :timeout {timeout_ms})']
    symbols = []
    for i, p in enumerate(left['params']):
        symbol = f'p{i}'
        symbols.append(symbol)
        sort = 'Bool' if p['type'] == 'bool' else '(_ BitVec 64)'
        lines.append(f'(declare-fun {symbol} () {sort})')
    first = Encoder('s', {p['name']: symbol for p, symbol in zip(left['params'], symbols)})
    second = Encoder('c', {p['name']: symbol for p, symbol in zip(right['params'], symbols)})
    sv, se = first.expr(left['body'])
    cv, ce = second.expr(right['body'])
    lines.extend(first.lines + second.lines)
    lines.extend([f'(assert (or (xor {se} {ce}) (and (not {se}) (not {ce}) (not (= {sv} {cv})))))', '(check-sat)'])
    return '\n'.join(lines) + '\n', symbols


def invoke(solver, query, timeout_ms):
    solver = Path(solver)
    require(solver.is_file(), 'Solver executable is unavailable', 'Unsupported', 'formal')
    try:
        result = subprocess.run([str(solver.resolve()), '-in', '-smt2'], input=query, text=True,
                                capture_output=True, timeout=timeout_ms / 1000 + 2)
    except subprocess.TimeoutExpired as exc:
        raise FoundationError('Timeout', 'Solver process exceeded budget', 'formal') from exc
    except OSError as exc:
        raise FoundationError('Unsupported', 'Solver cannot be executed', 'formal') from exc
    require(result.returncode == 0 and not result.stderr.strip(), 'Solver returned an operational error', 'Error', 'formal')
    return result.stdout.strip()


def sexpressions(text):
    tokens = re.findall(r'\(|\)|[^\s()]+', text)
    def parse(index):
        require(index < len(tokens), 'Truncated solver model')
        if tokens[index] != '(':
            require(tokens[index] != ')', 'Unexpected model delimiter')
            return tokens[index], index + 1
        value, index = [], index + 1
        while index < len(tokens) and tokens[index] != ')':
            child, index = parse(index)
            value.append(child)
        require(index < len(tokens), 'Unclosed solver model')
        return value, index + 1
    value, end = parse(0)
    require(end == len(tokens), 'Extra solver model output')
    return value


def decode_value(value, value_type):
    if value_type == 'bool':
        require(value in ('true', 'false'), 'Invalid solver boolean')
        return value == 'true'
    if isinstance(value, str) and re.fullmatch('#x[0-9a-fA-F]{16}', value):
        number = int(value[2:], 16)
    elif isinstance(value, str) and re.fullmatch('#b[01]{64}', value):
        number = int(value[2:], 2)
    elif isinstance(value, list) and len(value) == 3 and value[0] == '_' and value[2] == '64' and re.fullmatch('bv[0-9]+', value[1]):
        number = int(value[1][2:])
    else:
        raise FoundationError('InvalidEvidence', 'Unsupported solver bit-vector model', 'formal')
    require(0 <= number < (1 << 64), 'Model value outside bit-vector domain')
    return str(number - (1 << 64) if number >= (1 << 63) else number)


def solve(spec, candidate, solver, timeout_ms=10000):
    query, symbols = equivalence_query(spec, candidate, timeout_ms)
    status = invoke(solver, query, timeout_ms)
    if status == 'unsat':
        return {'outcome': 'Proved', 'evidence_class': 'solver_checked', 'query': query}
    if status == 'unknown':
        raise FoundationError('Unknown', 'Solver could not discharge the obligation', 'formal')
    require(status == 'sat', 'Unexpected solver response', 'InvalidEvidence', 'formal')
    arguments = []
    if symbols:
        output = invoke(solver, query + '(get-value (' + ' '.join(symbols) + '))\n', timeout_ms)
        require(output.startswith('sat\n'), 'Solver changed satisfiability during witness extraction')
        assignments = sexpressions(output[4:])
        require(isinstance(assignments, list) and all(isinstance(p, list) and len(p) == 2 for p in assignments), 'Malformed solver assignments')
        require([p[0] for p in assignments] == symbols, 'Solver witness symbols differ from query')
        arguments = [decode_value(pair[1], param['type']) for pair, param in zip(assignments, spec['function']['params'])]
    return {'outcome': 'Refuted', 'evidence_class': 'none', 'query': query, 'arguments': arguments}
