"""Restricted Resilient frontend: one total scalar function, no hidden bodies."""
from dataclasses import dataclass
import re

from .errors import FoundationError
from .ir import MAX_BYTES, MAX_DEPTH, MAX_NODES, binary, integer, node, program, require

TOKEN = re.compile(r'//[^\n]*|\s+|>=|<=|==|&&|\|\||->|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[(){};,<>+*/=:-]')
PRECEDENCE = {'||': 1, '&&': 2, '==': 3, '<': 4, '<=': 4, '>': 4, '>=': 4,
              '+': 5, '-': 5, '*': 6, '/': 6}
OP = {'||': 'or', '&&': 'and', '==': 'eq', '<': 'lt_signed', '<=': 'le_signed',
      '>': 'gt_signed', '>=': 'ge_signed', '+': 'add_wrap', '-': 'sub_wrap',
      '*': 'mul_wrap', '/': 'div_wrap'}
TYPES = {'int': 'i64', 'bool': 'bool'}
RESERVED = {'fn', 'return', 'if', 'else', 'int', 'bool', 'true', 'false'}


@dataclass
class Token:
    text: str
    start: int
    end: int


class Parser:
    def __init__(self, text):
        require(len(text.encode()) <= MAX_BYTES, 'Source exceeds byte budget', 'ResourceLimit', 'source')
        self.text, self.tokens, self.index = text, [], 0
        cursor = 0
        while cursor < len(text):
            match = TOKEN.match(text, cursor)
            require(match is not None, 'Unsupported source token', 'Unsupported', 'source', offset=cursor)
            value = match.group()
            if not value.isspace() and not value.startswith('//'):
                self.tokens.append(Token(value, cursor, match.end()))
            cursor = match.end()
        require(len(self.tokens) <= MAX_NODES, 'Source token budget exceeded', 'ResourceLimit', 'source')
        self.tokens.append(Token('<eof>', len(text), len(text)))
        self.params = {}

    def peek(self):
        return self.tokens[self.index].text

    def take(self, expected=None):
        token = self.tokens[self.index]
        require(token.text != '<eof>' and (expected is None or token.text == expected),
                'Expected ' + str(expected) + ', found ' + token.text, 'Unsupported', 'source', offset=token.start)
        self.index += 1
        return token

    def identifier(self):
        token = self.take()
        require(re.fullmatch('[A-Za-z][A-Za-z_0-9]*', token.text) is not None and token.text not in RESERVED,
                'Invalid scalar identifier', 'Unsupported', 'source', offset=token.start)
        return token.text

    def annotated(self, value, start, end):
        return {**value, '_span': [start, end]}

    def expression(self, minimum=0, depth=1):
        require(depth <= MAX_DEPTH, 'Source nesting budget exceeded', 'ResourceLimit', 'source')
        token = self.take()
        if token.text == '(':
            left = self.expression(depth=depth + 1)
            end = self.take(')').end
            left['_span'] = [token.start, end]
        elif token.text == '-' and self.peek().isdigit():
            literal = self.take()
            value = '-' + literal.text
            integer(value)
            left = self.annotated(node('int', 'i64', value=value), token.start, literal.end)
        elif token.text.isdigit():
            integer(token.text)
            left = self.annotated(node('int', 'i64', value=token.text), token.start, token.end)
        elif token.text in ('true', 'false'):
            left = self.annotated(node('bool', 'bool', value=token.text == 'true'), token.start, token.end)
        else:
            require(token.text in self.params, 'Unsupported expression or unbound variable', 'Unsupported', 'source', offset=token.start)
            left = self.annotated(node('var', self.params[token.text], name=token.text), token.start, token.end)
        while self.peek() in PRECEDENCE and PRECEDENCE[self.peek()] >= minimum:
            operator = self.take().text
            right = self.expression(PRECEDENCE[operator] + 1, depth + 1)
            left = self.annotated(binary(OP[operator], left, right), left['_span'][0], right['_span'][1])
        return left

    def block(self, depth=1):
        require(depth <= MAX_DEPTH, 'Source block budget exceeded', 'ResourceLimit', 'source')
        self.take('{')
        if self.peek() == 'return':
            self.take('return')
            body = self.expression(depth=depth)
            self.take(';')
        elif self.peek() == 'if':
            start = self.take('if').start
            condition = self.expression(depth=depth)
            yes = self.block(depth + 1)
            self.take('else')
            no = self.block(depth + 1)
            body = self.annotated(node('if', yes['type'], condition=condition, then=yes, **{'else': no}), start, self.tokens[self.index - 1].end)
        else:
            raise FoundationError('Unsupported', 'Only return or total if/else blocks are supported', 'source', offset=self.tokens[self.index].start)
        self.take('}')
        return body

    def parse(self):
        self.take('fn')
        name = self.identifier()
        self.take('(')
        parameters = []
        if self.peek() != ')':
            while True:
                scalar_type = self.take().text
                require(scalar_type in TYPES, 'Unsupported parameter type', 'Unsupported', 'source')
                parameter = self.identifier()
                require(parameter not in self.params, 'Duplicate parameter', stage='source')
                self.params[parameter] = TYPES[scalar_type]
                parameters.append({'name': parameter, 'type': TYPES[scalar_type]})
                if self.peek() != ',':
                    break
                self.take(',')
        self.take(')')
        self.take('->')
        return_type = self.take().text
        require(return_type in TYPES, 'Unsupported return type', 'Unsupported', 'source')
        body = self.block()
        require(self.peek() == '<eof>', 'Additional declarations or trailing code are unsupported', 'Unsupported', 'source', offset=self.tokens[self.index].start)
        spans = []
        def strip(value, path, depth=1):
            if isinstance(value, dict):
                require(depth <= MAX_DEPTH, 'Source expression depth budget exceeded', 'ResourceLimit', 'source')
                if '_span' in value:
                    start, end = value['_span']
                    spans.append({'ir_path': path, 'start': start, 'end': end, 'excerpt': self.text[start:end]})
                return {k: strip(v, path + '.' + k, depth + 1) for k, v in value.items() if k != '_span'}
            return value
        result = program(strip(body, 'function.body'), parameters, name)
        require(result['function']['return_type'] == TYPES[return_type], 'Declared return type mismatch', stage='source')
        return result, {'format': 'foundation-source-map-v1', 'spans': spans}


def parse_source(text):
    return Parser(text).parse()
