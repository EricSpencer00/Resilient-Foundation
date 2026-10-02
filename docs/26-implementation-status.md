# Current implementation

Checked 1 October 2026. The normative semantics remain in [the semantic core](05-semantic-core.md). This public checkout contains the archive's complete specification and the first supported end-to-end scalar route. The separate Resilient compiler repository remains unchanged.

## Working route

The dependency-free [foundation-core crate](../crates/foundation-core/Cargo.toml) validates every branch of typed i64/bool expressions and evaluates `scalar-wrapping-v1` observations. Arithmetic wraps at 64 bits, signed division truncates toward zero, MIN/-1 wraps to MIN, division by zero is an observable error, and booleans short circuit. Depth 64 and 4096 nodes are operational limits, not reductions of the i64 input domain.

The [Python frontend](../foundation/source.py) accepts one existing Resilient function signature with typed parameters, expressions and total return/if blocks. It rejects unknown tokens, helpers, loops, effects and extra declarations. The [wire adapter](../foundation/ir.py) rejects duplicate keys, imprecise numbers, incorrect types and unsupported nodes, and computes domain-separated canonical identities. Source maps bind expressions to original spans.

The [Resilient evidence adapter](../foundation/resilient.py) now provides a separate repository-boundary route. It inventories hashed compiler/runtime anchors, validates Resilient contract-certificate schema version 1 and SMT-LIB2 manifest hashes, regenerates supported pure definitions with the selected `rz` binary, and directly replays every SMT query with the selected Z3 executable. Its output remains `artifact_checked` without direct replay; replayed queries carry `solver_checked` evidence, while clauses without queries remain compiler-reported; it never upgrades the observed recovery, resource, temporal or embedded surfaces by implication.

The [intent adapter](../foundation/intent.py) accepts only `nonnegative-i64-v1`: the exact controlled request shipped in the example. Arbitrary prose returns `NeedsDecision`. The [solver route](../foundation/smt.py) asks real Z3 whether any declared i64/bool input distinguishes return values or division errors. UNSAT establishes all-input equivalence under the trusted encoding and solver. SAT witnesses replay through the Rust reference evaluator before being reported as `Refuted`.

The [restricted target reader](../foundation/native.py) independently decodes emitted Rust constructors into IR. The translation relation is rerun through Z3. Only the exact trusted runtime wrapper is accepted. Generated Rust runs the reference evaluator; this prototype is not direct optimized code generation or a verifier for arbitrary Rust.

The [capsule checker](../foundation/pipeline.py) reinterprets the request, reparses source, reconstructs both obligations, reruns Z3, checks profile/source/target/checker/tool hashes, recompiles native bytes and compares their digest. Execution repeats that gate, validates canonical inputs, copies the checked executable to private scratch, rechecks its hash, and compares its observation with reference execution. The supported policy is `scalar_source_exact_trusted_rust_v1`; `strict_native_exact` is `Unsupported`.

## Assurance boundaries

| Boundary | Current state | Remaining evidence |
|---|---|---|
| Prose to accepted requirements | One exact versioned controlled template | General intent validation and ambiguity decisions |
| Resilient source to typed IR | Restricted parser, source maps, independent conformance | Mechanized extraction preservation; wider language |
| Scalar expressions to observations | Rust reference evaluator and strict wire adapter | Mechanized semantics connection |
| Spec/candidate equivalence | Actual all-input QF_BV checks, Rust-replayed witnesses | Independent UNSAT kernel evidence |
| Result to checked evidence | Bound artifacts and reconstructed/rerun obligations | Proof-witness formats and incremental evidence DAG |
| IR to restricted Rust representation | Independent target decode and solver-checked relation | General Rust/bytecode translation |
| Rust source to native executable | Exact-byte rebuild and recorded toolchain | Native machine-code equivalence |
| Accepted artifact to execution | Guarded pure scalar native execution | Stateful recovery, effects, capabilities and deployment environments |
| LLM generation/evaluation | Frozen interactive Codex-authored candidate | Attested snapshots, model adapters, budgets and benchmarks |

`scalar-smt` and `translation-ir` are experimental, implemented routes bound to the recorded run. The Resilient contract/certificate boundary is an additional integration route, with its own explicit evidence class and replay requirement. Other backend routes remain planned. Work packages remain `in_progress` when this slice implements only part of their acceptance criteria. The existing illustrative bundle remains `NotAccepted`; its oracle and acceptance record were preserved.

## Recorded validation

The [actual NUC report](../validation/e2e.json) records 40 tests, zero failures and zero skips, five independently specified oracle executions, 50 in-process real solver invocations and 37 native compilations. CLI subprocess operations are additional and excluded from those counters. Three fault solver invocations check missing/unknown/timeout outcomes. Wrong branches, overflow, observable division errors, stale artifacts, hash-consistent forged queries/targets and inflated proof claims fail their required boundary. A semantically equivalent boundary mutant is accepted.

The report includes exact implementation, test, driver and evidence hashes, observed solver/Python/Rust identities and host architecture. Evidence excludes the executable itself and remains a host-specific audit record. Use a newly built capsule for execution. This conformance result is not a general soundness theorem, model score or performance benchmark.

## Reproduce and next gates

Follow [README commands](../README.md) and [the CLI contract](23-api-cli.md). `make check` runs specification consistency, Rust debug/release tests, lightweight Python tests, formatting and lint. `make e2e` runs the required real solver/native suite, rejects skips and saves evidence. Substantive runs belong on an authorized compute host. CI is configured for Rust 1.91.1 on Ubuntu; the observed NUC run used Rust 1.98.1. No hosted CI run is claimed for this branch.

Next gates are independent kernel evidence, a mechanized semantics connection and a restricted native relation. Verus/AutoVerus is a later adapter for Rust proof generation; its comparison and trust boundaries are in [the verifier research](../research/rust-verification-routes.md). Recovery, resource/probability routes and model evaluation retain their existing requirements.
