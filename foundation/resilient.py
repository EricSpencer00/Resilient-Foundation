"""Evidence adapter for the existing Resilient compiler.

This module deliberately stays at the repository boundary.  It inventories
the compiler from immutable source anchors, parses Resilient's published
certificate formats, regenerates them with a trusted compiler, and replays
every query with the explicitly selected Z3 executable.
It does not reimplement the Resilient parser, type checker, solver, or runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from .errors import FoundationError
from .ir import canonical, file_hash, write_json
from .source import Parser, TYPES


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "resilient-capabilities.json"
FORMAT = "foundation-resilient-evidence-v2"
INVENTORY_FORMAT = "foundation-resilient-inventory-v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 1024 * 1024
MAX_OBLIGATIONS = 512
LIMITATIONS = [
    "Solver evidence covers only the explicitly replayed SMT queries under Z3 trust.",
    "Source regeneration trusts the selected Resilient binary and its encoding; it is not a source-to-query theorem.",
    "Clauses without a query remain compiler-reported and carry no independent solver evidence.",
    "Signatures are retained as artifact identities, not authenticated by this adapter.",
    "Inventory anchors are selected source observations, not proof or execution coverage of those capabilities.",
]


ANCHORS = [
    "README.md",
    "LICENSE",
    "resilient/Cargo.toml",
    "resilient/src/lib.rs",
    "resilient/src/contract_certificate.rs",
    "resilient/src/contract_verify.rs",
    "resilient/src/cert_sign.rs",
    "resilient/src/cert_key.pem",
    "resilient/src/typechecker.rs",
    "resilient/src/recovery_checker.rs",
    "resilient/src/transaction_commit.rs",
    "resilient/src/idempotent_handler.rs",
    "resilient/src/noninterference.rs",
    "resilient/src/info_flow.rs",
    "resilient/src/probabilistic_contracts.rs",
    "resilient/src/power_contracts.rs",
    "resilient/src/wcet_contracts.rs",
    "resilient/src/tla_refines.rs",
    "resilient/src/tla_bridge.rs",
    "resilient/src/semantic_regression.rs",
    "resilient/src/mutation_testing.rs",
    "resilient/src/lsp_server.rs",
    "resilient/src/capabilities.rs",
    "resilient/src/rzbc_emit.rs",
    "resilient-runtime/Cargo.toml",
    "resilient-runtime/src/lib.rs",
    "resilient-runtime/src/vm.rs",
    "resilient-runtime/tla/runtime.tla",
    "docs/EMBEDDED_PIPELINE.md",
]


def _fail(reason: str, stage: str = "resilient", **details: Any) -> None:
    raise FoundationError("InvalidEvidence", reason, stage, **details)


def _artifact(path: Path, *, directory=False, limit=MAX_JSON_BYTES) -> Path:
    # Do this before resolving: resolve() erases a symlink at the input path.
    path = Path(os.path.abspath(path))
    if path.is_symlink() or not (path.is_dir() if directory else path.is_file()):
        _fail("Missing or symlinked Resilient artifact", path=str(path))
    if not directory and path.stat().st_size > limit:
        _fail("Oversized Resilient artifact", path=str(path))
    return path


def _strict_json(path: Path, limit: int = MAX_JSON_BYTES) -> Any:
    path = _artifact(path, limit=limit)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("Duplicate JSON key in Resilient artifact", key=key, path=str(path))
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(), object_pairs_hook=pairs,
                          parse_float=lambda value: (_ for _ in ()).throw(
                              ValueError("floating-point JSON is not accepted")),
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              ValueError("non-finite JSON is not accepted")))
    except (OSError, ValueError, RecursionError) as exc:
        _fail("Invalid Resilient JSON artifact: " + str(exc), path=str(path))


def _read_profile() -> dict[str, Any]:
    profile = _require_object(_strict_json(PROFILE), "Capability profile")
    if profile.get("kind") != "resilient_capabilities":
        _fail("Foundation Resilient capability profile has the wrong kind")
    return profile


def _git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and len(revision) == 40 else None


def inspect(root: Path) -> dict[str, Any]:
    """Return a deterministic inventory of the Resilient checkout.

    Missing anchors fail closed.  A successful inventory says that the
    implementation surface exists; it makes no claim that every capability
    has been proved or executed.
    """
    root = _artifact(root, directory=True)
    anchors = {}
    for relative in ANCHORS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            _fail("Resilient capability anchor is missing", anchor=relative)
        anchors[relative] = file_hash(path)
    profile = _read_profile()
    result: dict[str, Any] = {
        "format": INVENTORY_FORMAT,
        "profile_id": profile["integration_id"],
        "profile_sha256": file_hash(PROFILE),
        "resilient_revision": _git_revision(root),
        "anchors": anchors,
        "capability_ids": [cap["id"] for cap in profile["capabilities"]],
    }
    result["inventory_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(label + " must be an object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        _fail(label + " fields differ from the supported Resilient format",
              expected=sorted(expected), actual=sorted(value))


def _parse_contract_certificate(path: Path, source: Path) -> tuple[dict[str, Any], dict[str, int]]:
    certificate = _require_object(_strict_json(path), "Contract certificate")
    _require_exact_keys(certificate, {"schema", "schema_version", "source", "functions"},
                        "Contract certificate")
    if certificate["schema"] != "resilient-contract-certificate/v1" or type(certificate["schema_version"]) is not int or certificate["schema_version"] != 1:
        _fail("Unsupported Resilient contract certificate schema", stage="certificate")
    if not isinstance(certificate["source"], str) or not certificate["source"]:
        _fail("Resilient contract certificate source is invalid", stage="certificate")
    if Path(certificate["source"]).name != source.name:
        _fail("Contract certificate is bound to a different source filename",
              certificate_source=certificate["source"], source=source.name, stage="certificate")
    functions = certificate["functions"]
    if not isinstance(functions, list) or not functions or len(functions) > MAX_OBLIGATIONS:
        _fail("Contract certificate must contain at least one function", stage="certificate")
    counts = {"functions": 0, "clauses": 0, "pass": 0, "fail": 0, "unknown": 0}
    names = set()
    for function in functions:
        function = _require_object(function, "Certificate function")
        _require_exact_keys(function, {"name", "enrolled", "provenance", "clauses"},
                            "Certificate function")
        if not isinstance(function["name"], str) or not function["name"]:
            _fail("Certificate function name is invalid", stage="certificate")
        if function["name"] in names:
            _fail("Duplicate certificate function", stage="certificate")
        names.add(function["name"])
        if not isinstance(function["enrolled"], bool):
            _fail("Certificate enrolled flag is invalid", stage="certificate")
        if not isinstance(function["provenance"], list) or any(
                not isinstance(item, str) for item in function["provenance"]):
            _fail("Certificate provenance must be a string array", stage="certificate")
        clauses = function["clauses"]
        if not isinstance(clauses, list):
            _fail("Certificate clauses must be an array", stage="certificate")
        counts["functions"] += 1
        for clause in clauses:
            clause = _require_object(clause, "Certificate clause")
            required = {"clause", "kind", "verdict"}
            if not required <= set(clause):
                _fail("Certificate clause is missing required fields", stage="certificate")
            allowed = required | {"basis", "smtlib2", "counterexample"}
            if set(clause) - allowed:
                _fail("Certificate clause has unsupported fields", stage="certificate")
            if not isinstance(clause["clause"], str) or not isinstance(clause["kind"], str) or clause["kind"] not in {"requires", "ensures", "inferred_requires", "inferred_ensures"}:
                _fail("Certificate clause text or kind is invalid", stage="certificate")
            verdict = clause["verdict"]
            if not isinstance(verdict, str) or verdict not in {"pass", "fail", "unknown"}:
                _fail("Certificate clause verdict is invalid", stage="certificate")
            if "basis" in clause and (not isinstance(clause["basis"], str) or clause["basis"] not in {"implementation", "clause-only"}):
                _fail("Certificate basis is invalid", stage="certificate")
            if "smtlib2" in clause and not isinstance(clause["smtlib2"], str):
                _fail("Certificate SMT-LIB2 field is invalid", stage="certificate")
            if "counterexample" in clause and not isinstance(clause["counterexample"], str):
                _fail("Certificate counterexample field is invalid", stage="certificate")
            counts["clauses"] += 1
            if counts["clauses"] > MAX_OBLIGATIONS:
                _fail("Too many certificate clauses", stage="certificate")
            counts[verdict] += 1
    return certificate, counts


def _parse_manifest(directory: Path, source: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = directory / "manifest.json"
    manifest = _require_object(_strict_json(path), "Certificate manifest")
    _require_exact_keys(manifest, {"program", "obligations"}, "Certificate manifest")
    if not isinstance(manifest["program"], str) or Path(manifest["program"]).name != source.name:
        _fail("Certificate manifest is bound to a different source filename", stage="certificate")
    obligations = manifest["obligations"]
    if not isinstance(obligations, list) or not obligations or len(obligations) > MAX_OBLIGATIONS:
        _fail("Certificate manifest must contain a bounded nonempty obligation array", stage="certificate")
    records = []
    names, ids = set(), set()
    for obligation in obligations:
        obligation = _require_object(obligation, "Certificate obligation")
        required = {"fn", "kind", "idx", "cert", "sha256"}
        if not required <= set(obligation) or set(obligation) - (required | {"sig"}):
            _fail("Certificate obligation fields differ from Resilient's manifest", stage="certificate")
        name = obligation["cert"]
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9_-]+\.smt2", name) is None:
            _fail("Certificate filename is unsafe", stage="certificate")
        if any(not isinstance(obligation[key], str) or not obligation[key] for key in ("fn", "kind")) or type(obligation["idx"]) is not int or obligation["idx"] < 0:
            _fail("Invalid certificate obligation identity", stage="certificate")
        key = (obligation["fn"], obligation["kind"], obligation["idx"])
        if name in names or key in ids:
            _fail("Duplicate certificate obligation", stage="certificate")
        names.add(name)
        ids.add(key)
        cert_path = _artifact(directory / name)
        actual_hash = file_hash(cert_path)
        if obligation["sha256"] != actual_hash:
            _fail("Certificate SMT-LIB2 hash does not match manifest", certificate=name, stage="certificate")
        signature = obligation.get("sig")
        if signature is not None and (
                not isinstance(signature, str) or len(signature) != 128 or
                any(char not in "0123456789abcdefABCDEF" for char in signature)):
            _fail("Certificate obligation signature is malformed", certificate=name, stage="certificate")
        records.append({"certificate": name, "sha256": actual_hash,
                        "fn": obligation["fn"], "kind": obligation["kind"], "idx": obligation["idx"],
                        "signature": signature})
    if {p.name for p in directory.iterdir()} - (names | {"manifest.json", "cert.sig"}):
        _fail("Unlisted file in certificate directory", stage="certificate")
    return manifest, records


def _query(text: str) -> str:
    """Accept one bounded, non-interactive SMT query, with no output spoofing."""
    if not isinstance(text, str) or len(text.encode()) > MAX_JSON_BYTES:
        _fail("Missing or oversized SMT query", stage="certificate")
    tokens = re.findall(r';[^\n]*|"(?:[^\"]|\"\")*"|\|[^|]*\||[()]|[^\s();]+', text)
    tokens = [token for token in tokens if not token.startswith(";")]
    commands, current, depth = [], [], 0
    for token in tokens:
        if token == "(":
            depth += 1
            if depth > 256:
                _fail("SMT query nesting limit exceeded", stage="certificate")
        elif token == ")":
            depth -= 1
        elif depth == 0:
            _fail("SMT query contains text outside commands", stage="certificate")
        current.append(token)
        if depth < 0:
            _fail("Unbalanced SMT query", stage="certificate")
        if depth == 0:
            commands.append(current)
            current = []
    if depth or not commands or len(commands) > 4096:
        _fail("Unbalanced or oversized SMT command list", stage="certificate")
    allowed = {"set-logic", "set-info", "declare-const", "declare-fun", "define-fun", "assert", "check-sat"}
    if any(len(c) < 3 or c[1] not in allowed for c in commands):
        _fail("Unsupported SMT command (interactive/output commands are forbidden)", stage="certificate")
    if commands[-1] != ["(", "check-sat", ")"] or sum(c[1] == "check-sat" for c in commands) != 1:
        _fail("SMT query must end with exactly one check-sat", stage="certificate")
    return text


def _tool(path: Path, label: str) -> tuple[Path, dict[str, str]]:
    # Executable aliases (unlike proof artifacts) are permitted. Invoke exactly
    # the selected path; hash its target without turning a rustup shim into rustup.
    path = Path(os.path.abspath(path))
    if not path.is_file() or not os.access(path, os.X_OK):
        _fail(label + " executable is unavailable", stage="certificate")
    return path, {"name": path.name, "sha256": file_hash(path)}


def _invoke(command: list[str], *, query: str | None = None, timeout: int = 60):
    try:
        return subprocess.run(command, input=query, capture_output=True, text=True,
                              timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise FoundationError("Timeout", "Resilient evidence check timed out", "certificate") from exc
    except (OSError, UnicodeError) as exc:
        _fail("Evidence tool could not run: " + str(exc), stage="certificate")


def _definition_source(text: str) -> None:
    """Syntax gate for regeneration: pure definitions with no program actions.

    This gate shares the scalar frontend's lexer/return-if grammar. It does
    not assign scalar wrapping semantics to Resilient's contract encoding.
    The trusted Resilient compiler still checks types and emits the queries.
    """
    parser = Parser(text)
    names = set()
    while parser.peek() != "<eof>":
        parser.take("fn")
        name = parser.identifier()
        if name in names:
            _fail("Duplicate source function", stage="source")
        names.add(name)
        parser.params = {}
        parser.take("(")
        if parser.peek() != ")":
            while True:
                typ = parser.take().text
                if typ not in TYPES:
                    raise FoundationError("Unsupported", "Only scalar definition parameters are supported", "source")
                parameter = parser.identifier()
                if parameter in parser.params or parameter == "result":
                    _fail("Duplicate or reserved source parameter", stage="source")
                parser.params[parameter] = TYPES[typ]
                if parser.peek() != ",":
                    break
                parser.take(",")
        parser.take(")")
        parser.take("->")
        typ = parser.take().text
        if typ not in TYPES:
            raise FoundationError("Unsupported", "Only scalar definition results are supported", "source")
        params = dict(parser.params)
        while parser.peek() in {"requires", "ensures"}:
            kind = parser.take().text
            parser.params = {**params, **({"result": TYPES[typ]} if kind == "ensures" else {})}
            parser.expression()
        parser.params = params
        parser.block()
    if not names:
        _fail("Source contains no supported definitions", stage="source")


def _regenerate(source: Path, parsed: dict, manifest: dict, rz: Path) -> dict:
    binary, tool = _tool(rz, "Resilient")
    source_bytes = source.read_bytes()
    _definition_source(source_bytes.decode("utf-8"))
    with tempfile.TemporaryDirectory(prefix="foundation-resilient-regenerate-") as temporary:
        scratch = Path(temporary)
        candidate = scratch / source.name
        candidate.write_bytes(source_bytes)
        cert = scratch / "contract.json"
        proofs = scratch / "proofs"
        result = _invoke([str(binary), "--no-cache", "--typecheck", "--emit-contract-certificate",
                          str(cert), "--emit-certificate", str(proofs), str(candidate)])
        if result.returncode != 0:
            _fail("Resilient source regeneration failed", stage="certificate",
                  returncode=result.returncode, stderr=result.stderr[-2000:])
        fresh_cert, _ = _parse_contract_certificate(cert, candidate)
        fresh_manifest, _ = _parse_manifest(proofs, candidate)
        def contract(value):
            return {**value, "source": source.name}
        def obligations(value):
            return [{k: v for k, v in item.items() if k != "sig"} for item in value["obligations"]]
        if contract(parsed) != contract(fresh_cert) or obligations(manifest) != obligations(fresh_manifest):
            _fail("Imported artifacts differ from certificates regenerated from the current source", stage="certificate")
    return {"status": "regenerated", "compiler": tool,
            "profile": "pure-scalar-contract-definitions-v1"}


def _replay(queries: list[dict], z3: Path) -> dict:
    binary, tool = _tool(z3, "Z3")
    records = []
    for query in queries:
        result = _invoke([str(binary), "-in", "-smt2"], query=query["text"])
        response = result.stdout.strip()
        if result.returncode != 0 or result.stderr.strip():
            _fail("SMT solver failed", stage="certificate", returncode=result.returncode,
                  stdout=result.stdout[-2000:], stderr=result.stderr[-2000:])
        if response == "sat":
            raise FoundationError("Refuted", "Imported SMT query is satisfiable", "certificate", query=query["id"])
        if response == "unknown":
            raise FoundationError("Unknown", "SMT solver could not discharge the query", "certificate", query=query["id"])
        if response != "unsat":
            _fail("SMT solver did not return exactly one unsat result", stage="certificate", stdout=response[-2000:])
        records.append({"id": query["id"], "sha256": hashlib.sha256(query["text"].encode()).hexdigest(),
                        "result": "unsat"})
    if not records:
        _fail("No SMT queries were replayed", stage="certificate")
    return {"status": "passed", "solver": tool, "queries": records}


def import_evidence(resilient_root: Path, source: Path, certificate: Path,
                    certificate_dir: Path, rz: Path | None = None,
                    z3: Path | None = None, out: Path | None = None) -> dict[str, Any]:
    """Inventory artifacts, optionally regenerate source and replay queries.

    Imported bytes are associated with a filename until regeneration succeeds.
    Solver evidence always names individual queries, never every JSON clause.
    """
    source = _artifact(source, limit=MAX_SOURCE_BYTES)
    certificate = _artifact(certificate)
    certificate_dir = _artifact(certificate_dir, directory=True)
    inventory = inspect(resilient_root)
    parsed, counts = _parse_contract_certificate(certificate, source)
    manifest, proof_files = _parse_manifest(certificate_dir, source)
    if counts["fail"] or counts["unknown"]:
        _fail("Resilient contract certificate contains an open or failed clause", stage="certificate")
    queries = []
    compiler_reported = []
    for function in parsed["functions"]:
        for index, clause in enumerate(function["clauses"]):
            key = f"contract:{function['name']}:{index}:{clause['kind']}"
            if "smtlib2" in clause:
                queries.append({"id": key, "text": _query(clause["smtlib2"])})
            else:
                compiler_reported.append(key)
    for proof in proof_files:
        queries.append({"id": "manifest:" + proof["certificate"],
                        "text": _query((certificate_dir / proof["certificate"]).read_text())})
    signature_path = certificate_dir / "cert.sig"
    signature_hash = None
    if signature_path.exists() or signature_path.is_symlink():
        signature_path = _artifact(signature_path, limit=1024)
        # Resilient emits an Ed25519 batch signature as 128 hex characters.
        if re.fullmatch(r"[0-9a-fA-F]{128}", signature_path.read_text()) is None:
            _fail("Malformed batch signature", stage="certificate")
        signature_hash = file_hash(signature_path)
    binding = {"status": "associated_only", "compiler": None, "profile": None}
    if rz is not None:
        binding = _regenerate(source, parsed, manifest, rz)
    verification = {"status": "structural_only", "solver": None, "queries": []}
    if z3 is not None:
        verification = _replay(queries, z3)
    evidence = {
        "format": FORMAT,
        "integration_id": inventory["profile_id"],
        "source": {"name": source.name, "sha256": file_hash(source)},
        "source_binding": binding,
        "inventory": {"format": inventory["format"], "sha256": inventory["inventory_sha256"],
                      "resilient_revision": inventory["resilient_revision"],
                      "capability_ids": inventory["capability_ids"]},
        "contract_certificate": {"schema": parsed["schema"], "schema_version": parsed["schema_version"],
                                 "sha256": file_hash(certificate), "functions": counts["functions"],
                                 "clauses": counts["clauses"],
                                 "verdicts": {key: counts[key] for key in ("pass", "fail", "unknown")},
                                 "compiler_reported_only": compiler_reported},
        "proof_directory": {"manifest_sha256": file_hash(certificate_dir / "manifest.json"),
                            "obligations": proof_files, "batch_signature_present": signature_hash is not None,
                            "batch_signature_sha256": signature_hash, "authentication": "not_checked"},
        "verification": verification,
        "evidence_class": "solver_checked" if verification["status"] == "passed" else "artifact_checked",
        "claim_scope": "smt_queries" if verification["status"] == "passed" else "artifact_integrity",
        "limitations": LIMITATIONS,
    }
    if out is not None:
        write_json(out, evidence)
    return evidence


def verify_evidence(evidence_path: Path, resilient_root: Path, source: Path,
                    certificate: Path, certificate_dir: Path, rz: Path | None = None,
                    z3: Path | None = None) -> dict[str, Any]:
    """Recompute every field, including required assurance and tool identities."""
    evidence_path = _artifact(evidence_path)
    recorded = _require_object(_strict_json(evidence_path), "Foundation Resilient evidence")
    if recorded.get("format") != FORMAT:
        _fail("Unsupported Foundation Resilient evidence format; regenerate v2 evidence", stage="evidence")
    current = import_evidence(resilient_root, source, certificate, certificate_dir, rz, z3)
    if canonical(recorded) != canonical(current):
        _fail("Foundation Resilient evidence differs from the independently recomputed record", stage="evidence")
    return {"status": "passed", "format": "foundation-resilient-check-receipt-v2",
            "evidence_sha256": file_hash(evidence_path), "source_sha256": current["source"]["sha256"],
            "inventory_sha256": current["inventory"]["sha256"], "evidence_class": current["evidence_class"],
            "claim_scope": current["claim_scope"], "source_binding": current["source_binding"]["status"]}
