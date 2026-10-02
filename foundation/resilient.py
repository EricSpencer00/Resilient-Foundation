"""Evidence adapter for the existing Resilient compiler.

This module deliberately stays at the repository boundary.  It inventories
the compiler from immutable source anchors, parses Resilient's published
certificate formats, and asks the Resilient binary to replay SMT certificates.
It does not reimplement the Resilient parser, type checker, solver, or runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any

from .errors import FoundationError
from .ir import canonical, file_hash, write_json


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "resilient-capabilities.json"
FORMAT = "foundation-resilient-evidence-v1"
INVENTORY_FORMAT = "foundation-resilient-inventory-v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 1024 * 1024


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


def _safe_relative(path: str) -> bool:
    value = PurePosixPath(path)
    return not value.is_absolute() and ".." not in value.parts and bool(value.parts)


def _strict_json(path: Path, limit: int = MAX_JSON_BYTES) -> Any:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        _fail("Missing, symlinked, or oversized Resilient artifact", path=str(path))

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
    profile = _strict_json(PROFILE)
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
    root = Path(root).resolve()
    if not root.is_dir() or root.is_symlink():
        _fail("Resilient checkout is missing or symlinked", root=str(root))
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
    if certificate["schema"] != "resilient-contract-certificate/v1" or certificate["schema_version"] != 1:
        _fail("Unsupported Resilient contract certificate schema", stage="certificate")
    if not isinstance(certificate["source"], str) or not certificate["source"]:
        _fail("Resilient contract certificate source is invalid", stage="certificate")
    if Path(certificate["source"]).name != source.name:
        _fail("Contract certificate is bound to a different source filename",
              certificate_source=certificate["source"], source=source.name, stage="certificate")
    functions = certificate["functions"]
    if not isinstance(functions, list) or not functions:
        _fail("Contract certificate must contain at least one function", stage="certificate")
    counts = {"functions": 0, "clauses": 0, "pass": 0, "fail": 0, "unknown": 0}
    for function in functions:
        function = _require_object(function, "Certificate function")
        _require_exact_keys(function, {"name", "enrolled", "provenance", "clauses"},
                            "Certificate function")
        if not isinstance(function["name"], str) or not function["name"]:
            _fail("Certificate function name is invalid", stage="certificate")
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
            if not isinstance(clause["clause"], str) or not isinstance(clause["kind"], str):
                _fail("Certificate clause text or kind is invalid", stage="certificate")
            verdict = clause["verdict"]
            if verdict not in {"pass", "fail", "unknown"}:
                _fail("Certificate clause verdict is invalid", stage="certificate")
            if "smtlib2" in clause and not isinstance(clause["smtlib2"], str):
                _fail("Certificate SMT-LIB2 field is invalid", stage="certificate")
            if "counterexample" in clause and not isinstance(clause["counterexample"], str):
                _fail("Certificate counterexample field is invalid", stage="certificate")
            counts["clauses"] += 1
            counts[verdict] += 1
    return certificate, counts


def _parse_manifest(directory: Path, source: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = directory / "manifest.json"
    manifest = _require_object(_strict_json(path), "Certificate manifest")
    _require_exact_keys(manifest, {"program", "obligations"}, "Certificate manifest")
    if not isinstance(manifest["program"], str) or Path(manifest["program"]).name != source.name:
        _fail("Certificate manifest is bound to a different source filename", stage="certificate")
    obligations = manifest["obligations"]
    if not isinstance(obligations, list):
        _fail("Certificate manifest obligations must be an array", stage="certificate")
    records = []
    for obligation in obligations:
        obligation = _require_object(obligation, "Certificate obligation")
        required = {"fn", "kind", "idx", "cert", "sha256"}
        if not required <= set(obligation) or set(obligation) - (required | {"sig"}):
            _fail("Certificate obligation fields differ from Resilient's manifest", stage="certificate")
        name = obligation["cert"]
        if not isinstance(name, str) or not _safe_relative(name) or Path(name).suffix != ".smt2":
            _fail("Certificate filename is unsafe", stage="certificate")
        cert_path = directory / name
        if not cert_path.is_file() or cert_path.is_symlink():
            _fail("Certificate SMT-LIB2 file is missing", certificate=name, stage="certificate")
        actual_hash = file_hash(cert_path)
        if obligation["sha256"] != actual_hash:
            _fail("Certificate SMT-LIB2 hash does not match manifest", certificate=name, stage="certificate")
        signature = obligation.get("sig")
        if signature is not None and (
                not isinstance(signature, str) or len(signature) != 128 or
                any(char not in "0123456789abcdefABCDEF" for char in signature)):
            _fail("Certificate obligation signature is malformed", certificate=name, stage="certificate")
        records.append({"certificate": name, "sha256": actual_hash, "signed": signature is not None})
    return manifest, records


def verify_certificate_dir(directory: Path, rz: Path, z3: Path | None = None,
                           timeout: int = 60) -> dict[str, Any]:
    """Ask Resilient to replay its manifest, hashes, signatures and SMT files."""
    directory = Path(directory).resolve()
    rz = Path(rz).resolve()
    if not rz.is_file() or rz.is_symlink():
        _fail("Resilient verifier binary is unavailable", stage="certificate")
    command = [str(rz), "verify-all", str(directory)]
    if z3 is not None:
        z3 = Path(z3).resolve()
        if not z3.is_file() or z3.is_symlink():
            _fail("Z3 verifier binary is unavailable", stage="certificate")
        command.append("--z3")
    environment = os.environ.copy()
    if z3 is not None:
        environment["PATH"] = str(z3.parent) + os.pathsep + environment.get("PATH", "")
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout, check=False, env=environment)
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail("Resilient certificate replay could not run: " + str(exc), stage="certificate")
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "command": [Path(item).name if item.startswith("/") else item for item in command],
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "z3_replay_requested": z3 is not None,
    }


def import_evidence(resilient_root: Path, source: Path, certificate: Path,
                    certificate_dir: Path, rz: Path | None = None,
                    z3: Path | None = None, out: Path | None = None) -> dict[str, Any]:
    """Bind a Resilient contract certificate to source and replay artifacts."""
    resilient_root = Path(resilient_root).resolve()
    source = Path(source).resolve()
    certificate = Path(certificate).resolve()
    certificate_dir = Path(certificate_dir).resolve()
    if not source.is_file() or source.is_symlink() or source.stat().st_size > MAX_SOURCE_BYTES:
        _fail("Resilient source is missing, symlinked, or oversized", stage="source")
    inventory = inspect(resilient_root)
    parsed, counts = _parse_contract_certificate(certificate, source)
    manifest, proof_files = _parse_manifest(certificate_dir, source)
    verification = {"status": "structural_only", "z3_replay_requested": False}
    if rz is not None:
        verification = verify_certificate_dir(certificate_dir, rz, z3)
        if verification["status"] != "passed":
            _fail("Resilient certificate replay failed", stage="certificate",
                  verification=verification)
    signatures = (certificate_dir / "cert.sig").is_file()
    evidence = {
        "format": FORMAT,
        "integration_id": inventory["profile_id"],
        "source": {"name": source.name, "sha256": file_hash(source)},
        "inventory": {
            "format": inventory["format"],
            "sha256": inventory["inventory_sha256"],
            "resilient_revision": inventory["resilient_revision"],
            "capability_ids": inventory["capability_ids"],
        },
        "contract_certificate": {
            "schema": parsed["schema"],
            "schema_version": parsed["schema_version"],
            "sha256": file_hash(certificate),
            "functions": counts["functions"],
            "clauses": counts["clauses"],
            "verdicts": {key: counts[key] for key in ("pass", "fail", "unknown")},
        },
        "proof_directory": {
            "manifest_sha256": file_hash(certificate_dir / "manifest.json"),
            "obligations": proof_files,
            "batch_signature_present": signatures,
        },
        "verification": verification,
        "evidence_class": "solver_checked" if verification["status"] == "passed" and verification["z3_replay_requested"] else "artifact_checked",
        "limitations": [
            "The Resilient compiler and Z3 remain trusted producers/checkers for this imported route.",
            "A certificate authenticates proof artifacts; it does not prove source-to-query preservation by itself.",
            "Capabilities in the inventory are observed from source anchors unless an explicit evidence report names them.",
        ],
    }
    if counts["fail"] or counts["unknown"]:
        _fail("Resilient contract certificate contains an open or failed clause", stage="certificate",
              verdicts=evidence["contract_certificate"]["verdicts"])
    if out is not None:
        write_json(out, evidence)
    return evidence


def verify_evidence(evidence_path: Path, resilient_root: Path, source: Path,
                    certificate: Path, certificate_dir: Path, rz: Path | None = None,
                    z3: Path | None = None) -> dict[str, Any]:
    """Recompute an imported record and reject stale source or proof bytes."""
    evidence_path = Path(evidence_path).resolve()
    recorded = _require_object(_strict_json(evidence_path), "Foundation Resilient evidence")
    if recorded.get("format") != FORMAT:
        _fail("Unsupported Foundation Resilient evidence format", stage="evidence")
    current = import_evidence(resilient_root, source, certificate, certificate_dir, rz, z3)
    for section in ("source", "inventory", "contract_certificate", "proof_directory"):
        if recorded.get(section) != current.get(section):
            _fail("Foundation Resilient evidence is stale: " + section, stage="evidence")
    return {"status": "passed", "format": "foundation-resilient-check-receipt-v1",
            "evidence_sha256": file_hash(evidence_path),
            "source_sha256": current["source"]["sha256"],
            "inventory_sha256": current["inventory"]["sha256"],
            "evidence_class": current["evidence_class"]}
