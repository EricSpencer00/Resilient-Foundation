# Resilient Foundation

A Rust-based foundation for AI-generated software whose requirements, executable specifications, implementation, translation evidence and runtime behavior remain connected.

**Status: private scalar end-to-end prototype, version 0.1.0-draft, 1 October 2026.** A controlled requirement and restricted Resilient candidate now pass through typed IR, all-input Z3 equivalence, checked Rust constructor translation, artifact-bound acceptance and guarded native execution. The recorded NUC run passed all 36 conformance checks with no skips. Z3 and Rust compilation remain trusted; kernel proofs, native machine-code equivalence, stateful effects and model benchmarks remain planned.

The first frontend is [Resilient](https://github.com/EricSpencer00/Resilient), owned by Eric Spencer. Resilient keeps its language/compiler/runtime identity; Foundation supplies shared semantic profiles, obligations, evidence and evaluation protocols.

## The central contract

For a complete deterministic executable specification, accepted implementation and declared environment, the target is equality of **observable behaviors**. The correspondence includes values, errors, effect ordering and termination under the declared bounds. It is not a correspondence between source lines or every internal instruction.

Free-form language becomes an explicit requirement ledger. Controlled language and versioned templates can have exact formal interpretations. An LLM's interpretation of unrestricted prose remains a candidate requiring validation or an accepted decision. That boundary is recorded, never silently converted into a theorem.

## Read this first

1. [Normative specification index](SPEC.md).
2. [Correctness contract](docs/02-correctness-contract.md).
3. [Intent and autoformalization](docs/03-intent-and-autoformalization.md).
4. [Translation and native execution](docs/06-translation-and-codegen.md).
5. [Evaluation matrix](docs/15-evaluation-matrix.md), [model protocol](docs/16-model-evaluation.md), [SWE-bench route](docs/17-swebench.md), and [package performance](docs/18-package-performance.md).
6. [Roadmap and acceptance gates](docs/21-roadmap.md).
7. [Machine-readable work packages](roadmap/work-packages.json).
8. [Current implementation and next gates](docs/26-implementation-status.md), and [Rust verifier comparison](research/rust-verification-routes.md).

## Validate the specification

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_spec.py
~~~

This checks schema validity, artifact bindings, traceability, backlog dependencies, examples and deliberately invalid evidence manifests. Experimental backend declarations must bind to the saved conformance report and unchanged implementation, tests and evidence. This read-only consistency check does not rerun solvers or accept program capsules.

## Run the Rust prototype

With Rust 1.85 or newer (tested with 1.91.1):

~~~sh
cargo run --locked -p foundation-core --example nonnegative
make check
~~~

The example evaluates the five independently specified boundary inputs. `make check` runs specification checks, Rust conformance tests in debug and release modes, validator policy tests, lightweight Python frontend/translation tests, formatting and lint checks. The solver/native tests require `make e2e`; their skips in the lightweight suite are explicit. It uses the local `.venv` when present. The Rust crate has no third-party dependencies and does not call a model or solver.

## Run the end-to-end path

Use a compute host with Python 3.10+, the pinned development requirements, Z3, and Rust 1.85+. Run from the repository root; on the coordinator Mac, offload the full gate to an authorized compute host.

~~~sh
.venv/bin/python -m foundation build \
  --request examples/e2e/nonnegative/request.txt \
  --candidate examples/e2e/nonnegative/candidate.rz \
  --out artifacts/nonnegative
.venv/bin/python -m foundation check artifacts/nonnegative
.venv/bin/python -m foundation run artifacts/nonnegative --input '{"x":"-7"}'
make e2e
~~~

The execution returns `"0"` and identifies the exact accepted capsule and native executable. Tool paths can be set with global `--solver`, `--cargo` and `--rustc` options before the subcommand. `bin/foundation` is also available when the Python environment is active. An existing output directory is preserved; use a fresh path for each build.

The supported policy is `scalar_source_exact_trusted_rust_v1`. It accepts one exact controlled nonnegative requirement template and a pure i64/bool source fragment. Other prose returns `NeedsDecision`; unsupported source and stronger native policies fail explicitly. Generated Rust constructs the expression model and runs the tested reference evaluator. [The CLI contract](docs/23-api-cli.md) describes outcomes and remaining limits.

[Saved evidence](validation/e2e.json) records actual tool identities, test/source hashes, solver calls, native compilations, five frozen oracle executions and a replayed counterexample. It is a host-specific record; rebuild a capsule to execute it. The candidate was authored by Codex during this task; no attested model snapshot or model benchmark is claimed.

## First implementation slice

The first slice starts with typed i64/bool expressions, wrapping arithmetic, explicit division errors, signed comparisons, short-circuit boolean operators and `if`. The Rust API checks every branch before evaluating a concrete input. Strict JSON loading, Resilient extraction with source spans, scalar equivalence and restricted Rust translation checks are implemented. Statements beyond total return/if blocks, loops, contracts, arbitrary Rust and recovery effects remain outside this route. Recovery adds defined reset/snapshot boundaries and retry-safe effects in later work packages.

The eventual platform supports general agent programs through typed capabilities and modular verified components. Existing unverified libraries, neural models and external systems remain explicit interfaces with declared assumptions. They do not inherit a whole-system proof from a verified wrapper.

## Evaluation philosophy

Keep separate: **repository tests passed**, **formal contracts proved**, **translation evidence checked**, **intent validated**, **coverage achieved**, and **cost/performance**. New models are evaluated against pinned suites and budgets; package changes are evaluated on fixed artifacts independent of the model.

The scalar end-to-end route has recorded conformance evidence. No current model score, performance speedup, mechanized compiler theorem or whole-system native proof is claimed.
