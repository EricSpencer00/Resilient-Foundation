"""Strict scalar wire format and domain-separated artifact identity."""
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator

from .errors import FoundationError

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'scalar-wrapping-v1'
VERSION = '0.1.0-draft'
MIN_I64, MAX_I64 = -(1 << 63), (1 << 63) - 1
MAX_BYTES, MAX_DEPTH, MAX_NODES = 65536, 64, 4096
OPS = {'add_wrap', 'sub_wrap', 'mul_wrap', 'div_wrap', 'eq',
       'lt_signed', 'le_signed', 'gt_signed', 'ge_signed', 'and', 'or'}


def require(condition, reason, outcome='InvalidEvidence', stage='validation', **details):
    if not condition:
        raise FoundationError(outcome, reason, stage, **details)


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def forbidden_number(text):
    raise FoundationError('InvalidEvidence', 'Floating/non-finite JSON numbers are unsupported: ' + text)


def loads(text):
    require(len(text.encode('utf-8')) <= MAX_BYTES, 'JSON input exceeds byte budget', 'ResourceLimit')
    try:
        return json.loads(text, object_pairs_hook=pairs_unique,
                          parse_float=forbidden_number, parse_constant=forbidden_number)
    except (ValueError, RecursionError) as exc:
        raise FoundationError('InvalidEvidence', 'Invalid JSON: ' + str(exc)) from exc


def load(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= MAX_BYTES,
            'Missing or oversized JSON artifact: ' + path.name)
    return loads(path.read_text())


def canonical(value):
    def check(item):
        if isinstance(item, dict):
            require(all(isinstance(k, str) and k.isascii() for k in item), 'Canonical keys must be ASCII')
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
        else:
            require(item is None or isinstance(item, (str, bool, int)), 'Unsupported canonical value')
    check(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def identity(kind, value):
    require(re.fullmatch('[a-z][a-z0-9-]*', kind) is not None, 'Invalid identity domain')
    return hashlib.sha256(('foundation:' + kind + ':v1\0').encode() + canonical(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def integer(text):
    require(isinstance(text, str) and re.fullmatch(r'0|-[1-9][0-9]*|[1-9][0-9]*', text) is not None,
            'i64 values must be canonical decimal strings')
    require(len(text) <= 20, 'Integer outside i64')
    value = int(text)
    require(MIN_I64 <= value <= MAX_I64, 'Integer outside i64')
    return value


def infer(expr, params, depth=1, nodes=None):
    if nodes is None:
        nodes = [0]
    nodes[0] += 1
    require(depth <= MAX_DEPTH and nodes[0] <= MAX_NODES, 'Expression exceeds operational budget', 'ResourceLimit')
    require(isinstance(expr, dict), 'Expression must be an object')
    kind = expr.get('kind')
    require(kind in ('int', 'bool', 'var', 'binary', 'if'), 'Unsupported expression kind', 'Unsupported')
    require(expr.get('type') in ('i64', 'bool'), 'Unsupported expression type', 'Unsupported')
    if kind == 'int':
        integer(expr.get('value'))
        actual = 'i64'
    elif kind == 'bool':
        require(isinstance(expr.get('value'), bool), 'Boolean literal must be bool')
        actual = 'bool'
    elif kind == 'var':
        require(expr.get('name') in params, 'Unbound variable: ' + str(expr.get('name')))
        actual = params[expr['name']]
    elif kind == 'if':
        require(infer(expr.get('condition'), params, depth + 1, nodes) == 'bool', 'Condition must be bool')
        actual = infer(expr.get('then'), params, depth + 1, nodes)
        require(actual == infer(expr.get('else'), params, depth + 1, nodes), 'Branch types differ')
    else:
        op = expr.get('op')
        require(op in OPS, 'Unsupported binary operation', 'Unsupported')
        left = infer(expr.get('left'), params, depth + 1, nodes)
        right = infer(expr.get('right'), params, depth + 1, nodes)
        require(left == right, 'Operand types differ')
        if op in ('and', 'or'):
            require(left == 'bool', 'Boolean operands must be bool')
            actual = 'bool'
        elif op == 'eq':
            actual = 'bool'
        else:
            require(left == 'i64', 'Numeric operands must be i64')
            actual = 'bool' if op.endswith('_signed') else 'i64'
    require(expr['type'] == actual, 'Declared expression type differs from inferred type')
    return actual


def validate_program(program, actual=False):
    require(isinstance(program, dict), 'Program must be an object')
    require(program.get('semantic_profile_id') == PROFILE, 'Unsupported semantic profile', 'Unsupported')
    function = program.get('function', {})
    require(isinstance(function, dict) and isinstance(function.get('params'), list), 'Invalid function signature')
    params = {}
    for param in function['params']:
        require(isinstance(param, dict) and isinstance(param.get('name'), str), 'Invalid parameter')
        require(param.get('type') in ('i64', 'bool'), 'Unsupported parameter type', 'Unsupported')
        require(param['name'] not in params, 'Duplicate parameter: ' + param['name'])
        params[param['name']] = param['type']
    require(len(params) <= 16, 'Parameter count exceeds budget', 'ResourceLimit')
    require(infer(function.get('body'), params) == function.get('return_type'), 'Return type mismatch')
    schema = json.loads((ROOT / 'schemas/program-ir.schema.json').read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(program), key=lambda e: str(e.path))
    require(not errors, 'Program schema mismatch: ' + (errors[0].message if errors else ''))
    if actual:
        require(program['illustrative'] is False, 'Illustrative artifacts cannot be accepted')
    return program


def node(kind, value_type, **fields):
    return {'kind': kind, 'type': value_type, **fields}


def binary(op, left, right):
    value_type = 'bool' if op in ('eq', 'and', 'or') or op.endswith('_signed') else 'i64'
    return node('binary', value_type, op=op, left=left, right=right)


def program(body, params, name='candidate', artifact_id='candidate'):
    result = {'version': VERSION, 'kind': 'scalar_program', 'illustrative': False,
              'id': artifact_id, 'semantic_profile_id': PROFILE,
              'function': {'name': name, 'params': params, 'return_type': body['type'], 'body': body}}
    return validate_program(result, actual=True)


def inputs(program, values):
    params = program['function']['params']
    require(isinstance(values, dict) and set(values) == {p['name'] for p in params}, 'Input keys differ from signature')
    arguments = []
    for param in params:
        value = values[param['name']]
        if param['type'] == 'i64':
            integer(value)
        else:
            require(isinstance(value, bool), 'Boolean input must be bool')
        arguments.append(value)
    return arguments
