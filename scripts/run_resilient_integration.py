#!/usr/bin/env python3
"""Run the cross-repository Resilient certificate acceptance gate.

This is intentionally opt-in.  Building the separate Resilient compiler and
its Z3 feature is a substantive workload and belongs on an authorized compute
host, while the public GitHub workflow remains a free Foundation-only gate.
"""

import argparse
import json
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from foundation.errors import FoundationError
from foundation.ir import file_hash
from foundation.resilient import import_evidence, inspect, verify_evidence

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, timeout=900, cwd=None, env=None):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"command failed to run: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"command exited {result.returncode}: {' '.join(map(str, command))}\n"
            f"stdout:\n{result.stdout[-4000:]}\nstderr:\n{result.stderr[-4000:]}"
        )
    return {"command": [str(item) for item in command], "seconds": round(time.monotonic() - started, 3),
            "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resilient-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--cargo", default=os.environ.get("FOUNDATION_CARGO") or shutil.which("cargo"))
    parser.add_argument("--rustc", default=os.environ.get("FOUNDATION_RUSTC") or shutil.which("rustc"))
    parser.add_argument("--z3", default=os.environ.get("FOUNDATION_Z3") or shutil.which("z3"), type=Path)
    parser.add_argument("--rz", type=Path)
    parser.add_argument("--timeout", default=900, type=int)
    args = parser.parse_args()

    root = args.resilient_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not args.cargo or not args.rustc or not args.z3:
        raise RuntimeError("cargo, rustc and z3 are required for the Resilient integration gate")
    cargo = Path(args.cargo).resolve()
    rustc = Path(args.rustc).resolve()
    z3 = Path(args.z3).resolve()
    if args.rz:
        rz = args.rz.resolve()
    else:
        rz = root / "target" / "release" / "rz"
    source = root / "resilient" / "examples" / "foundation_cert_demo.rz"
    fixture = Path(__file__).resolve().parents[1] / "examples" / "resilient" / "cert_demo_pass.rz"
    certificate = out / "contract-certificate.json"
    cert_dir = out / "proofs"
    evidence_path = out / "evidence.json"
    if not fixture.is_file():
        raise RuntimeError("Foundation Resilient fixture is missing: " + str(fixture))
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fixture, source)

    inventory = inspect(root)
    build_env = dict(os.environ)
    build_env["RUSTC"] = str(rustc)
    build = run([str(cargo), "build", "--manifest-path", str(root / "resilient" / "Cargo.toml"),
                 "--release", "--locked", "--features", "z3"], timeout=args.timeout, env=build_env)
    if not rz.is_file():
        raise RuntimeError("Resilient release binary was not produced: " + str(rz))
    emit = run([str(rz), "--no-cache", "--typecheck", "--emit-contract-certificate", str(certificate),
                "--emit-certificate", str(cert_dir), str(source)], timeout=args.timeout)
    replay = run([str(rz), "verify-all", str(cert_dir), "--z3"], timeout=120)
    evidence = import_evidence(root, source, certificate, cert_dir, rz, z3, evidence_path)

    with tempfile.TemporaryDirectory(prefix="foundation-resilient-mutation-") as scratch:
        mutated = Path(scratch) / source.name
        mutated.write_bytes(source.read_bytes() + b"\n// mutation: stale source must be rejected\n")
        try:
            verify_evidence(evidence_path, root, mutated, certificate, cert_dir, rz, z3)
        except FoundationError as error:
            mutation = {"status": "rejected", "outcome": error.outcome, "reason": error.reason}
        else:
            raise RuntimeError("source mutation was not rejected by the evidence binding")

    implementation_paths = [
        "foundation/resilient.py", "foundation/cli.py", "foundation/errors.py",
        "foundation/ir.py", "profiles/resilient-capabilities.json",
        "schemas/resilient-capabilities.schema.json", "schemas/resilient-integration-report.schema.json",
        "profiles/backend-capabilities.json", "scripts/validate_spec.py",
        "examples/resilient/cert_demo_pass.rz",
    ]
    test_paths = ["tests/test_resilient.py"]
    driver_paths = ["scripts/run_resilient_integration.py"]
    implementation_hashes = {path: file_hash(ROOT / path) for path in implementation_paths}
    test_hashes = {path: file_hash(ROOT / path) for path in test_paths}
    driver_hashes = {path: file_hash(ROOT / path) for path in driver_paths}
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    evidence_files = {
        "validation/resilient/evidence.json": file_hash(evidence_path),
        "validation/resilient/contract-certificate.json": file_hash(certificate),
        "validation/resilient/proofs/manifest.json": file_hash(cert_dir / "manifest.json"),
    }
    for proof in sorted(cert_dir.glob("*.smt2")):
        evidence_files["validation/resilient/proofs/" + proof.name] = file_hash(proof)
    report = {
        "version": "0.1.0-draft",
        "kind": "resilient_integration_report",
        "format": "foundation-resilient-integration-report-v1",
        "status": "passed",
        "scope": "resilient_contract_certificate_e2e",
        "evidence_class": evidence["evidence_class"],
        "capability_ids": inventory["capability_ids"],
        "inventory_sha256": inventory["inventory_sha256"],
        "source_sha256": file_hash(source),
        "certificate_sha256": file_hash(certificate),
        "proof_manifest_sha256": evidence["proof_directory"]["manifest_sha256"],
        "build": {"cargo": str(cargo), "rustc": str(rustc), **build},
        "emit": emit,
        "replay": replay,
        "mutation": mutation,
        "implementation_hashes": implementation_hashes,
        "test_hashes": test_hashes,
        "driver_hashes": driver_hashes,
        "evidence_files": evidence_files,
        "tests_run": 4,
        "tests_failed": 0,
        "tests_skipped": 0,
        "assumptions": evidence["limitations"],
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (FoundationError, RuntimeError, OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "reason": str(error)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
