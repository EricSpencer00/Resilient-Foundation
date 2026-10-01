# Current implementation

Checked 30 September 2026. This is a prototype status record; the normative semantics remain in [the semantic core](05-semantic-core.md).

The private GitHub checkout was missing the validator, requirement registry, roadmap, research catalog and evaluation manifests present in the supplied MacBook archive. Those artifacts were imported while preserving matching tracked files and the Git history. No change was made in the separate Resilient compiler repository.

## Working scalar slice

The dependency-free [foundation-core crate](../crates/foundation-core/Cargo.toml) implements a typed Rust expression API for `scalar-wrapping-v1`. `Program::validate` checks the profile, unique parameter bindings, variable bindings, operand/branch types and return type. It visits all branches, even when a concrete input would not reach them. `Program::evaluate` validates first, checks argument types/count, then evaluates pure scalar observations.

Supported expressions are i64/bool literals, variables, binary operations and `if`. Add/subtract/multiply wrap at 64 bits. Division truncates toward zero, returns `DivideByZero` for zero divisors and wraps MIN/-1 to MIN. Signed comparisons, typed equality and short-circuit boolean operators preserve the profile. `parse_i64_decimal` accepts canonical decimal strings without conversion through floating point.

The evaluator limits expression depth to 64 and total nodes to 4096. Exceeding either yields `ResourceLimit` before execution. These are operational cutoffs, not a reduction of the i64 input domain or a proved termination bound. AST construction, allocation and destruction remain the caller's responsibility. The Rust API cannot represent unknown expression variants; rejecting unknown JSON nodes belongs to the future adapter.

The [conformance suite](../crates/foundation-core/tests/scalar_conformance.rs) uses independently specified boundary values and error observations. The nonnegative API case uses the five cases from the existing [oracle](../examples/nonnegative/oracle.json); neither that oracle nor the illustrative acceptance status was changed.

## Assurance boundaries

| Boundary | Current state | Remaining evidence |
|---|---|---|
| Prose to accepted requirements | Draft specification and illustrative ledger | Intent validation and ambiguity decisions |
| Resilient source to typed IR | Planned | WP-05 extraction, source maps and independent lowering cases |
| Typed scalar expressions to observations | Implemented Rust reference evaluator; conformance tested | JSON wire adapter, canonical identity and mechanized semantics connection |
| Spec/candidate equivalence | Planned | WP-06 actual solver route, all-input relation and witness replay |
| Proof result to checked evidence | Planned | WP-07 actual checking and artifact binding |
| IR to Rust/bytecode/native artifact | Planned | WP-08 and WP-12 through WP-14 translation evidence |
| Recovery, effects and runtime execution | Planned | Reachable reset states, effect protocols and execution capsules |
| LLM generation and evaluation | Planned | Frozen tasks/oracles, model snapshots, budgets and separate metrics |

No solver, proof kernel, model or generated-program runtime is invoked by the current checks. Ordinary Rust compilation is trusted. Concrete evaluation does not create `Proved`, `Accepted` or execution authorization. The illustrative bundle remains `NotAccepted` and no backend capability was promoted.

The scalar profile's implementation metadata now records the reference evaluator, without changing arithmetic or observations. The illustrative bundle's profile hash was refreshed to match those bytes. This rebinds the example; it does not create evidence for a proof result.

## Reproduce

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
make check
cargo run --locked -p foundation-core --example nonnegative
~~~

Tested with rustc/cargo 1.91.1 on the MacBook. The small crate compiles in under a second locally. CI is configured for Rust 1.91.1 on Ubuntu, but no hosted CI run has been observed for this branch. Sustained solver builds, benchmarks and model work must use an authorized remote compute host.

## Next gates

WP-03 and WP-04 are in progress. Add strict JSON-to-typed-IR loading and domain-separated canonical identity, then connect Resilient extraction through WP-05. Implement one bit-precise scalar solver route under WP-06 before enabling LLM proof repair or acceptance. Follow with checked evidence and translation validation. The [Rust verifier comparison](../research/rust-verification-routes.md) records the external routes and their separate trust boundaries.
