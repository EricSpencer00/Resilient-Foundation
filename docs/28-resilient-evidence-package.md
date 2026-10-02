# Resilient evidence package

Checked 1 October 2026. Foundation connects to [Resilient](https://github.com/EricSpencer00/Resilient) through its certificate formats. The compiler remains a separate project.

```text
Selected compiler source anchors -> inventory
Current pure function definitions -> trusted rz regeneration -> matching artifacts
Contract queries + manifest queries -> selected Z3 executable -> per-query evidence
All identities and claims -> complete record -> independent recomputation
```

`foundation resilient inspect` hashes the selected compiler and runtime anchors and capability profile. This is a selected-source fingerprint, not a complete build identity or evidence that every capability was executed. The selected `rz` and Z3 executable bytes have their own identities.

```sh
.venv/bin/python -m foundation resilient import-cert \
  --root /path/to/Resilient \
  --source /path/to/cert_demo_pass.rz \
  --certificate /tmp/cert/contract.json \
  --certificate-dir /tmp/cert/proofs \
  --rz /path/to/Resilient/target/release/rz \
  --z3 /usr/bin/z3 \
  --out /tmp/foundation-resilient-evidence.json
```

The v2 record has separate `source_binding` and `verification` results. Without `--rz`, source bytes are only associated with the imported filename. With `--rz`, Foundation copies the current source into a fresh temporary directory, regenerates both certificate formats and requires their contents to match. Only source path spelling and optional signature material are excluded from the regeneration comparison. Certificate generation accepts scalar function definitions with return/if bodies and requires/ensures expressions; it rejects calls, imports, attributes, top-level actions and other unsupported syntax before invoking the compiler. It does not execute function bodies. Resilient's type checker and mathematical contract encoding remain trusted; this is not a source-to-query or wrapping-i64 preservation theorem.

`--z3` independently replays every embedded contract query and every manifest query, even without `--rz`. Each must contain one final `check-sat`, use supported noninteractive SMT commands, and return exactly `unsat`. Output commands, solver errors, missing tools, SAT, Unknown and timeout prevent acceptance. `solver_checked` applies only to the listed query identities. A `pass` clause without a query appears under `compiler_reported_only` and gains no solver claim. The record never authorizes the scalar route's guarded native execution.

The adapter rejects duplicate keys, unsupported versions and fields, malformed types, unsafe or duplicate proof identities, empty manifests, unlisted files, symlinked inputs, stale hashes and failed/open clauses. Signature material is hashed and retained, with `authentication: not_checked`; a signature is not a proof. `verify-evidence` regenerates the entire record and compares every field, including tool identities, assurance and scope. Required replay cannot silently be omitted. Old v1 records must be regenerated. Full records bind the selected tools and checkout identities; regenerate them for a different host or checkout. Portable query replay records the solver it actually uses.

The cross-repository gate uses a fresh output directory and leaves upstream examples untouched:

```sh
.venv/bin/python scripts/run_resilient_integration.py \
  --resilient-root /path/to/Resilient --out /tmp/fresh-acceptance
```

It builds a z3-enabled compiler unless `--rz` selects a prebuilt trusted binary, then tests current-source regeneration, direct replay, stale reimport, altered source identity, forged assurance, omitted replay, satisfiable queries and output spoofing. Its test count comes from the executed regression suite and named acceptance cases. Reusing an output directory fails instead of overwriting it. Cargo/rustc aliases retain their invoked basename so rustup shims work.

GitHub CI replays the saved real SMT queries with `scripts/replay_resilient.py` on a standard public runner. That portable gate checks artifact/query identities and solver results; it does not rerun the large Resilient build or prove the compiler encoding. Recovery/effects, information flow, resources/probability, TLA/refinement, embedded runtime and developer tooling stay inventoried until their own semantic acceptance gates exist. The recorded integration run claims only source frontend, contract-query verification and proof artifacts.
