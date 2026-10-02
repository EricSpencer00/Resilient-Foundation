"""Checked Rust constructor lowering using the reference runtime.

The constructor decoder is a restricted target reader, not a general Rust parser.
Native compilation, runtime/OS/hardware remain explicitly trusted.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .errors import FoundationError
from .ir import ROOT, binary, file_hash, integer, loads, node, program, require, validate_program

BEGIN, END = '/* FOUNDATION_MODEL_BEGIN */', '/* FOUNDATION_MODEL_END */'
RUST_OP = {'add_wrap': 'AddWrap', 'sub_wrap': 'SubWrap', 'mul_wrap': 'MulWrap', 'div_wrap': 'DivWrap',
           'eq': 'Eq', 'lt_signed': 'LtSigned', 'le_signed': 'LeSigned', 'gt_signed': 'GtSigned',
           'ge_signed': 'GeSigned', 'and': 'And', 'or': 'Or'}
# Independently declared target meanings; a changed emitter mapping is checked.
TARGET_OP = {'AddWrap': 'add_wrap', 'SubWrap': 'sub_wrap', 'MulWrap': 'mul_wrap', 'DivWrap': 'div_wrap',
             'Eq': 'eq', 'LtSigned': 'lt_signed', 'LeSigned': 'le_signed', 'GtSigned': 'gt_signed',
             'GeSigned': 'ge_signed', 'And': 'and', 'Or': 'or'}
RUST_TYPE = {'i64': 'I64', 'bool': 'Bool'}
TARGET_TYPE = {'I64': 'i64', 'Bool': 'bool'}


def template():
    return (ROOT / 'runtime/scalar-runner.rs.in').read_text()


def quoted(text):
    return json.dumps(text, ensure_ascii=True) + '.into()'


def rust_expr(expr):
    kind = expr['kind']
    if kind == 'int':
        return 'Expr::Int(' + expr['value'] + 'i64)'
    if kind == 'bool':
        return 'Expr::Bool(' + str(expr['value']).lower() + ')'
    if kind == 'var':
        return 'Expr::Var(' + quoted(expr['name']) + ')'
    if kind == 'binary':
        return ('Expr::Binary{op:BinaryOp::' + RUST_OP[expr['op']] + ',left:Box::new(' + rust_expr(expr['left'])
                + '),right:Box::new(' + rust_expr(expr['right']) + ')}')
    return ('Expr::If{condition:Box::new(' + rust_expr(expr['condition']) + '),then_branch:Box::new('
            + rust_expr(expr['then']) + '),else_branch:Box::new(' + rust_expr(expr['else']) + ')}')


def emit(model):
    validate_program(model, actual=True)
    function = model['function']
    params = ','.join('Parameter{name:' + quoted(p['name']) + ',value_type:Type::' + RUST_TYPE[p['type']] + '}'
                      for p in function['params'])
    body = ('Program{semantic_profile_id:' + quoted(model['semantic_profile_id']) + ',parameters:vec![' + params
            + '],return_type:Type::' + RUST_TYPE[function['return_type']] + ',body:' + rust_expr(function['body']) + '}')
    return template().replace('@MODEL@', body)


LEX = re.compile(r'\s+|"(?:[^"\\]|\\.)*"|::|-?[0-9]+i64|[A-Za-z_][A-Za-z_0-9]*|[{}\[\],().:!]')


class ConstructorReader:
    def __init__(self, text):
        self.tokens, self.index, cursor = [], 0, 0
        while cursor < len(text):
            match = LEX.match(text, cursor)
            require(match is not None, 'Unsupported Rust target token', 'Unsupported', 'translation')
            if not match.group().isspace():
                self.tokens.append(match.group())
            cursor = match.end()

    def peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else '<eof>'

    def take(self, expected=None):
        value = self.peek()
        require(value != '<eof>' and (expected is None or value == expected),
                'Unsupported Rust constructor syntax', 'Unsupported', 'translation')
        self.index += 1
        return value

    def tokens_exact(self, *tokens):
        for token in tokens:
            self.take(token)

    def string(self):
        value = self.take()
        require(value.startswith('"'), 'Expected target string', 'Unsupported', 'translation')
        text = json.loads(value)
        self.tokens_exact('.', 'into', '(', ')')
        return text

    def scalar_type(self):
        self.tokens_exact('Type', '::')
        value = self.take()
        require(value in TARGET_TYPE, 'Unsupported Rust target type', 'Unsupported', 'translation')
        return TARGET_TYPE[value]

    def boxed(self, depth):
        self.tokens_exact('Box', '::', 'new', '(')
        value = self.expr(depth + 1)
        self.take(')')
        return value

    def expr(self, depth=1):
        require(depth <= 64, 'Rust target depth budget exceeded', 'ResourceLimit', 'translation')
        self.tokens_exact('Expr', '::')
        kind = self.take()
        if kind == 'Int':
            self.take('(')
            value = self.take()
            require(value.endswith('i64'), 'Target literal must be i64')
            integer(value[:-3])
            self.take(')')
            return node('int', 'i64', value=value[:-3])
        if kind == 'Bool':
            self.take('(')
            value = self.take()
            require(value in ('true', 'false'), 'Target boolean is invalid')
            self.take(')')
            return node('bool', 'bool', value=value == 'true')
        if kind == 'Var':
            self.take('(')
            name = self.string()
            self.take(')')
            require(name in self.params, 'Unbound target variable')
            return node('var', self.params[name], name=name)
        if kind == 'Binary':
            self.tokens_exact('{', 'op', ':', 'BinaryOp', '::')
            operator = self.take()
            require(operator in TARGET_OP, 'Unsupported Rust target operator', 'Unsupported', 'translation')
            self.tokens_exact(',', 'left', ':')
            left = self.boxed(depth)
            self.tokens_exact(',', 'right', ':')
            right = self.boxed(depth)
            self.take('}')
            return binary(TARGET_OP[operator], left, right)
        require(kind == 'If', 'Unsupported Rust target expression', 'Unsupported', 'translation')
        self.tokens_exact('{', 'condition', ':')
        condition = self.boxed(depth)
        self.tokens_exact(',', 'then_branch', ':')
        yes = self.boxed(depth)
        self.tokens_exact(',', 'else_branch', ':')
        no = self.boxed(depth)
        self.take('}')
        return node('if', yes['type'], condition=condition, then=yes, **{'else': no})

    def read(self):
        self.tokens_exact('Program', '{', 'semantic_profile_id', ':')
        profile = self.string()
        self.tokens_exact(',', 'parameters', ':', 'vec', '!', '[')
        parameters, self.params = [], {}
        if self.peek() != ']':
            while True:
                self.tokens_exact('Parameter', '{', 'name', ':')
                name = self.string()
                self.tokens_exact(',', 'value_type', ':')
                value_type = self.scalar_type()
                self.take('}')
                require(name not in self.params, 'Duplicate Rust target parameter')
                self.params[name] = value_type
                parameters.append({'name': name, 'type': value_type})
                if self.peek() != ',':
                    break
                self.take(',')
        self.tokens_exact(']', ',', 'return_type', ':')
        return_type = self.scalar_type()
        self.tokens_exact(',', 'body', ':')
        body = self.expr()
        self.take('}')
        require(self.peek() == '<eof>', 'Trailing Rust target code', 'Unsupported', 'translation')
        model = program(body, parameters, 'translated', 'translated')
        require(profile == model['semantic_profile_id'] and return_type == body['type'], 'Rust target profile/type mismatch')
        return model


def decode(source):
    require(len(source.encode()) <= 262144, 'Rust target exceeds budget', 'ResourceLimit', 'translation')
    require(source.count(BEGIN) == source.count(END) == 1, 'Target model boundary is invalid')
    prefix, rest = source.split(BEGIN)
    model, suffix = rest.split(END)
    expected_prefix, expected_rest = template().split(BEGIN)
    _, expected_suffix = expected_rest.split(END)
    require(prefix == expected_prefix and suffix == expected_suffix, 'Target runtime wrapper was changed')
    return ConstructorReader(model).read()


def tool_run(arguments, cwd=None, timeout=60, env=None):
    try:
        result = subprocess.run([str(a) for a in arguments], cwd=cwd, env=env,
                                capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise FoundationError('Timeout', 'Native tool budget exceeded', 'native') from exc
    except OSError as exc:
        raise FoundationError('Unsupported', 'Native tool unavailable', 'native') from exc
    require(result.returncode == 0, 'Native tool failed: ' + result.stderr[-1500:], 'Error', 'native')
    return result


class NativeTools:
    def __init__(self, cargo=None, rustc=None):
        self.cargo = cargo or shutil.which('cargo')
        self.rustc = rustc or shutil.which('rustc')
        require(self.cargo and self.rustc, 'Rust toolchain is unavailable', 'Unsupported', 'native')

    def build_core(self):
        compiler = shutil.which(str(self.rustc)) or os.path.abspath(self.rustc)
        environment = dict(os.environ, RUSTC=compiler)
        tool_run([self.cargo, 'build', '--release', '--locked', '-p', 'foundation-core',
                  '--manifest-path', ROOT / 'Cargo.toml'], timeout=60, env=environment)

    def identity(self):
        version = tool_run([self.rustc, '-vV']).stdout.strip()
        return {'rustc_verbose_version': version, 'flags': ['--edition=2024', '-Copt-level=2', '-Cdebuginfo=0'],
                'core_source_sha256': file_hash(ROOT / 'crates/foundation-core/src/lib.rs'),
                'runner_sha256': file_hash(ROOT / 'runtime/scalar-runner.rs.in'),
                'core_library_sha256': file_hash(ROOT / 'target/release/libfoundation_core.rlib')}

    def compile(self, directory, output='native'):
        directory = Path(directory)
        decode((directory / 'generated.rs').read_text())
        tool_run([self.rustc, '--edition=2024', '--crate-name', 'foundation_capsule', '-C', 'opt-level=2', '-C', 'debuginfo=0',
                  '--extern', 'foundation_core=' + str(ROOT / 'target/release/libfoundation_core.rlib'),
                  '-L', 'dependency=' + str(ROOT / 'target/release/deps'), 'generated.rs', '-o', output], cwd=directory)
        return directory / output

    def evaluate(self, model, arguments):
        with tempfile.TemporaryDirectory(prefix='foundation-reference-') as scratch:
            directory = Path(scratch)
            source = emit(model)
            decoded = decode(source)
            require(decoded['function']['params'] == model['function']['params']
                    and decoded['function']['body'] == model['function']['body'], 'Reference bridge changed IR')
            (directory / 'generated.rs').write_text(source)
            binary_path = self.compile(directory)
            return execute(binary_path, arguments)


def execute(binary_path, arguments):
    command = [Path(binary_path).resolve()] + [str(v).lower() if isinstance(v, bool) else v for v in arguments]
    output = tool_run(command, timeout=5).stdout.strip()
    observation = loads(output)
    require(isinstance(observation, dict) and observation.get('kind') in ('return', 'error'), 'Native observation is invalid')
    if observation['kind'] == 'error':
        require(observation == {'kind': 'error', 'error': 'DivideByZero'}, 'Unknown native domain error')
    elif observation.get('type') == 'i64':
        require(set(observation) == {'kind', 'type', 'value'}, 'Invalid native value fields')
        integer(observation['value'])
    else:
        require(set(observation) == {'kind', 'type', 'value'} and observation.get('type') == 'bool'
                and isinstance(observation.get('value'), bool), 'Invalid native boolean')
    return observation
