# Resilient evidence package

Checked 1 October 2026. This package treats [Resilient](https://github.com/EricSpencer00/Resilient) as an external compiler and runtime, then gives its existing verification surfaces a stable Foundation boundary. Foundation does not copy the compiler or quietly restate its claims.

The integration has one connected path:

~~~text
Resilient checkout
    -> source-anchor inventory
    -> rz --emit-contract-certificate + --emit-certificate
    -> manifest/hash validation
    -> rz verify-all --z3
    -> Foundation evidence record
~~~

The inventory is produced by `foundation resilient inspect`. It binds the Resilient and `resilient-runtime` Cargo manifests, compiler entry point, contract verifier, certificate implementation, recovery/effects, noninterference, resource, temporal, embedded-runtime, mutation and tooling modules. Each anchor is hashed. The resulting inventory is a repository fingerprint and capability map; it is not a proof of every listed surface.

The import command is:

~~~sh
.venv/bin/python -m foundation resilient import-cert \
  --root /path/to/Resilient \
  --source /path/to/Resilient/resilient/examples/foundation_cert_demo.rz \
  --certificate /tmp/cert/contract.json \
  --certificate-dir /tmp/cert/proofs \
  --rz /path/to/Resilient/target/release/rz \
  --z3 /usr/bin/z3 \
  --out /tmp/foundation-resilient-evidence.json
~~~

The adapter accepts only Resilient contract-certificate schema version 1. It rejects duplicate JSON keys, floating-point JSON, unsupported fields, unsafe proof paths, missing SMT-LIB2 files, stale hashes, source filename mismatches and `fail`/`unknown` clauses. When `--rz` is supplied, `rz verify-all --z3` must pass before the record can be marked `solver_checked`. Without a replay command, the record remains `artifact_checked`. A batch signature is recorded when present; signature verification is delegated to the Resilient binary, and no signing key is stored here.

The capability profile separates what is integrated from what is only observed. Contract verification and certificate import are connected to the Foundation evidence graph. Resilient's recovery/effect, noninterference, WCET/power/probability, TLA/refinement, no-std runtime, mutation and LSP surfaces are catalogued with explicit limitations until each gets its own semantic profile, independent checker and acceptance report. The scalar Foundation route remains the only route that can authorize the existing guarded native execution policy.

The independent runner in `scripts/run_resilient_integration.py` is the cross-repository acceptance gate. It builds a z3-enabled `rz`, emits the contract and SMT-LIB2 artifacts, asks Resilient to replay them with Z3, imports the evidence, mutates the source, and confirms the source binding rejects the stale certificate. Run it on the authorized compute host; the public GitHub workflow stays free and does not build the separate Resilient repository by default.
