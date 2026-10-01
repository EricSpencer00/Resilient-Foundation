"""Artifact-bound scalar evidence and guarded native execution."""
from pathlib import Path
import shutil
import subprocess
import tempfile

from .errors import FoundationError
from .intent import interpret
from .ir import ROOT, canonical, file_hash, identity, inputs, load, require, validate_program, write_json
from .native import NativeTools, decode, emit, execute
from .smt import equivalence_query, solve
from .source import parse_source

POLICY = 'scalar_source_exact_trusted_rust_v1'
FORMAT = 'foundation-capsule-v1'
SCOPE = {'semantic_profile_id': 'scalar-wrapping-v1', 'domain': 'all inputs of declared i64/bool signature',
         'observations': ['return_value', 'DivideByZero', 'termination'], 'fragment': 'pure_total_scalar_expressions'}
INTENT = {'mode': 'controlled_language', 'status': 'accepted', 'template': 'nonnegative-i64-v1'}
FILES = ['request.txt', 'requirements.json', 'spec-ir.json', 'candidate.rz', 'candidate-ir.json',
         'source-map.json', 'profile.json', 'generated.rs', 'translation-ir.json', 'formal.smt2',
         'translation.smt2', 'native']
TCB_FILES = ['foundation/ir.py', 'foundation/source.py', 'foundation/intent.py', 'foundation/smt.py',
             'foundation/native.py', 'foundation/pipeline.py', 'foundation/cli.py', 'foundation/errors.py',
             'foundation/__main__.py', 'bin/foundation', 'schemas/program-ir.schema.json', 'runtime/scalar-runner.rs.in',
             'crates/foundation-core/src/lib.rs', 'crates/foundation-core/Cargo.toml', 'Cargo.toml', 'Cargo.lock']
ASSUMPTIONS = [
    'Versioned controlled template interpretation and restricted Resilient parser.',
    'Typed scalar model and QF_BV encoding; Z3 is trusted, no independent UNSAT proof kernel.',
    'Restricted Rust constructor decoder and tested foundation-core reference runtime.',
    'Recorded rustc/LLVM compilation, standard library, OS and hardware.',
    'Native source executes through the reference evaluator; this is not direct optimized code generation.',
]


def implementation_identity():
    return {name: file_hash(ROOT / name) for name in TCB_FILES}


def solver_identity(solver):
    solver = Path(solver)
    require(solver.is_file(), 'Solver is unavailable', 'Unsupported', 'formal')
    try:
        result = subprocess.run([str(solver.resolve()), '--version'], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FoundationError('Unsupported', 'Solver identity cannot be read', 'formal') from exc
    require(result.returncode == 0 and result.stdout.strip(), 'Invalid solver identity', 'Unsupported', 'formal')
    return {'version': result.stdout.strip(), 'executable_sha256': file_hash(solver)}


def replay_refutation(spec, candidate, result, native):
    arguments = result['arguments']
    first = native.evaluate(spec, arguments)
    second = native.evaluate(candidate, arguments)
    require(first != second, 'Solver counterexample does not replay through Rust reference semantics', stage='formal')
    return {'arguments': arguments, 'spec_observation': first, 'candidate_observation': second,
            'replay': 'rust_reference_runtime', 'validated': True}


def build(request, candidate_source, output, solver, native=None, policy=POLICY, timeout_ms=10000):
    require(policy == POLICY, 'Requested assurance policy is unsupported; native-machine checking is unavailable', 'Unsupported', 'policy')
    spec, ledger = interpret(request)
    candidate, source_map = parse_source(candidate_source)
    native = native or NativeTools()
    native.build_core()
    output = Path(output)
    require(not output.exists(), 'Output directory already exists', 'Error', 'artifact')
    output.mkdir(parents=True)
    (output / 'request.txt').write_text(request)
    (output / 'candidate.rz').write_text(candidate_source)
    write_json(output / 'requirements.json', ledger)
    write_json(output / 'spec-ir.json', spec)
    write_json(output / 'candidate-ir.json', candidate)
    write_json(output / 'source-map.json', source_map)
    shutil.copyfile(ROOT / 'profiles/scalar-wrapping-v1.json', output / 'profile.json')
    formal = solve(spec, candidate, solver, timeout_ms)
    (output / 'formal.smt2').write_text(formal['query'])
    if formal['outcome'] == 'Refuted':
        witness = replay_refutation(spec, candidate, formal, native)
        write_json(output / 'counterexample.json', witness)
        raise FoundationError('Refuted', 'Candidate differs from the locked specification', 'formal', counterexample=witness)
    source = emit(candidate)
    (output / 'generated.rs').write_text(source)
    target = decode(source)
    write_json(output / 'translation-ir.json', target)
    translation = solve(candidate, target, solver, timeout_ms)
    (output / 'translation.smt2').write_text(translation['query'])
    if translation['outcome'] == 'Refuted':
        witness = replay_refutation(candidate, target, translation, native)
        raise FoundationError('InvalidEvidence', 'Rust lowering changed observations', 'translation', counterexample=witness)
    native.compile(output)
    evidence = {
        'format': FORMAT, 'policy': POLICY, 'acceptance': 'Accepted',
        'intent': INTENT,
        'scope': SCOPE,
        'formal': {'outcome': 'Proved', 'evidence_class': 'solver_checked', 'obligation': 'spec_candidate_observable_equivalence'},
        'translation': {'outcome': 'Proved', 'evidence_class': 'translation_checked', 'basis': 'solver_checked',
                        'obligation': 'candidate_restricted_rust_constructor_equivalence'},
        'native': {'relation': 'trusted_compilation', 'toolchain': native.identity()},
        'solver': solver_identity(solver), 'solver_timeout_ms': timeout_ms,
        'artifact_hashes': {name: file_hash(output / name) for name in FILES},
        'canonical_identities': {'spec': identity('program-ir', spec), 'candidate': identity('program-ir', candidate),
                                 'translation': identity('program-ir', target)},
        'implementation_hashes': implementation_identity(), 'assumptions': ASSUMPTIONS,
        'generation': {'role': 'untrusted_candidate_producer', 'candidate_source_sha256': file_hash(output / 'candidate.rz'),
                       'model_snapshot': 'not_attested', 'model_evaluation': 'not_run'},
    }
    write_json(output / 'capsule.json', evidence)
    receipt, _ = check(output, solver, native)
    write_json(output / 'check-receipt.json', receipt)
    return receipt


def check(directory, solver, native=None, policy=POLICY):
    require(policy == POLICY, 'Requested assurance policy is unsupported', 'Unsupported', 'policy')
    directory = Path(directory).resolve()
    require((directory / 'capsule.json').is_file() and not (directory / 'capsule.json').is_symlink(), 'Capsule manifest is missing or unsafe')
    evidence = load(directory / 'capsule.json')
    require(isinstance(evidence, dict), 'Capsule manifest must be an object')
    require(set(evidence) == {'format', 'policy', 'acceptance', 'intent', 'scope', 'formal', 'translation', 'native',
                              'solver', 'solver_timeout_ms', 'artifact_hashes', 'canonical_identities',
                              'implementation_hashes', 'assumptions', 'generation'}, 'Capsule fields differ from supported format')
    require(evidence.get('format') == FORMAT and evidence.get('policy') == POLICY and evidence.get('acceptance') == 'Accepted', 'Capsule policy/acceptance is invalid')
    require(evidence.get('intent') == INTENT and evidence.get('scope') == SCOPE, 'Intent or proof scope differs from supported route')
    require(evidence.get('formal') == {'outcome': 'Proved', 'evidence_class': 'solver_checked', 'obligation': 'spec_candidate_observable_equivalence'}, 'Unsupported formal evidence declaration')
    require(evidence.get('translation') == {'outcome': 'Proved', 'evidence_class': 'translation_checked', 'basis': 'solver_checked',
                                          'obligation': 'candidate_restricted_rust_constructor_equivalence'}, 'Unsupported translation evidence declaration')
    require(evidence.get('assumptions') == ASSUMPTIONS and evidence.get('implementation_hashes') == implementation_identity(), 'Checker assumptions or implementation changed')
    hashes = evidence.get('artifact_hashes', {})
    require(isinstance(hashes, dict), 'Capsule artifact bindings must be an object')
    require(set(hashes) == set(FILES), 'Capsule artifact set differs from policy')
    for name in FILES:
        path = directory / name
        require(path.is_file() and not path.is_symlink() and file_hash(path) == hashes[name], 'Stale or changed artifact: ' + name)
    require(evidence.get('generation') == {'role': 'untrusted_candidate_producer', 'candidate_source_sha256': hashes['candidate.rz'],
                                         'model_snapshot': 'not_attested', 'model_evaluation': 'not_run'}, 'Unsupported generation provenance claim')
    require((directory / 'profile.json').read_bytes() == (ROOT / 'profiles/scalar-wrapping-v1.json').read_bytes(), 'Semantic profile changed')
    spec, ledger = interpret((directory / 'request.txt').read_text())
    candidate, source_map = parse_source((directory / 'candidate.rz').read_text())
    target = decode((directory / 'generated.rs').read_text())
    for name, expected in [('spec-ir.json', spec), ('requirements.json', ledger), ('candidate-ir.json', candidate),
                           ('source-map.json', source_map), ('translation-ir.json', target)]:
        require(canonical(load(directory / name)) == canonical(expected), 'Source/model binding differs: ' + name)
    identities = {'spec': identity('program-ir', spec), 'candidate': identity('program-ir', candidate), 'translation': identity('program-ir', target)}
    require(evidence.get('canonical_identities') == identities, 'Canonical artifact identity differs')
    timeout = evidence.get('solver_timeout_ms')
    require(type(timeout) is int and 1 <= timeout <= 60000, 'Invalid evidence solver budget')
    require(evidence.get('solver') == solver_identity(solver), 'Solver identity changed')
    native = native or NativeTools()
    native.build_core()
    for filename, first, second in [('formal.smt2', spec, candidate), ('translation.smt2', candidate, target)]:
        expected_query, _ = equivalence_query(first, second, timeout)
        require((directory / filename).read_text() == expected_query, 'Query is not derived from the bound models: ' + filename)
        actual = solve(first, second, solver, timeout)
        require(actual['outcome'] == 'Proved', 'Claimed proof does not hold on independently reconstructed obligation')
    require(evidence.get('native') == {'relation': 'trusted_compilation', 'toolchain': native.identity()}, 'Native toolchain/runtime binding differs')
    with tempfile.TemporaryDirectory(prefix='foundation-native-check-') as scratch:
        scratch = Path(scratch)
        (scratch / 'generated.rs').write_bytes((directory / 'generated.rs').read_bytes())
        rebuilt = native.compile(scratch)
        require(file_hash(rebuilt) == hashes['native'], 'Native bytes do not match the accepted source/toolchain')
    receipt = {'format': 'foundation-check-receipt-v1', 'outcome': 'Proved', 'acceptance': 'Accepted', 'policy': POLICY,
               'formal_evidence_class': 'solver_checked', 'translation_evidence_class': 'translation_checked',
               'native_relation': 'trusted_compilation', 'capsule_sha256': file_hash(directory / 'capsule.json'),
               'checked_artifacts': hashes, 'assumptions': ASSUMPTIONS}
    return receipt, {'spec': spec, 'candidate': candidate, 'evidence': evidence}


def run(directory, values, solver, native=None, policy=POLICY):
    native = native or NativeTools()
    receipt, context = check(directory, solver, native, policy)
    spec_args = inputs(context['spec'], values)
    candidate_values = {p['name']: value for p, value in zip(context['candidate']['function']['params'], spec_args)}
    candidate_args = inputs(context['candidate'], candidate_values)
    reference = native.evaluate(context['spec'], spec_args)
    with tempfile.TemporaryDirectory(prefix='foundation-execute-') as scratch:
        trusted_binary = Path(scratch) / 'native'
        shutil.copyfile(Path(directory) / 'native', trusted_binary)
        require(file_hash(trusted_binary) == receipt['checked_artifacts']['native'], 'Native artifact changed before execution')
        trusted_binary.chmod(0o700)
        observation = execute(trusted_binary, candidate_args)
    require(observation == reference, 'Native execution differs from reference observation', stage='runtime')
    return {'format': 'foundation-execution-v1', 'outcome': 'Executed', 'policy': POLICY,
            'runtime_status': 'DeployedBound', 'capsule_sha256': receipt['capsule_sha256'],
            'native_sha256': receipt['checked_artifacts']['native'], 'inputs': values,
            'observation': observation, 'reference_observation': reference, 'assumptions': ASSUMPTIONS}
