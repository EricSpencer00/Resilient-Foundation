"""Deterministic source generation for accepted scalar intent."""
from .errors import FoundationError
from .intent import SENTENCE, interpret
from .ir import require, validate_program
from .source import parse_source

OPERATORS = {
    'add_wrap': '+', 'sub_wrap': '-', 'mul_wrap': '*', 'div_wrap': '/',
    'eq': '==', 'lt_signed': '<', 'le_signed': '<=', 'gt_signed': '>',
    'ge_signed': '>=', 'and': '&&', 'or': '||',
}


def expression(expr):
    kind = expr['kind']
    if kind == 'int':
        return expr['value']
    if kind == 'bool':
        return str(expr['value']).lower()
    if kind == 'var':
        return expr['name']
    if kind == 'binary':
        return '(' + expression(expr['left']) + ' ' + OPERATORS[expr['op']] + ' ' + expression(expr['right']) + ')'
    raise FoundationError('Unsupported', 'Conditional expression is outside the source expression fragment', 'generation')


def statement(expr):
    if expr['kind'] == 'if':
        return ('if ' + expression(expr['condition']) + ' { ' + statement(expr['then'])
                + ' } else { ' + statement(expr['else']) + ' }')
    return 'return ' + expression(expr) + ';'


def render_source(spec):
    validate_program(spec, actual=True)
    accepted, _ = interpret(SENTENCE)
    require(spec == accepted, 'Only the accepted nonnegative-i64-v1 template can be synthesized',
            'Unsupported', 'generation')
    function = spec['function']
    params = ', '.join(('int' if p['type'] == 'i64' else 'bool') + ' ' + p['name'] for p in function['params'])
    result = 'int' if function['return_type'] == 'i64' else 'bool'
    source = 'fn ' + function['name'] + '(' + params + ') -> ' + result + ' { ' + statement(function['body']) + ' }\n'
    parsed, _ = parse_source(source)
    require(parsed['function'] == function, 'Generated Resilient source changed the locked formal function',
            'InvalidEvidence', 'generation')
    return source
