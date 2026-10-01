# System architecture

## Component graph

~~~mermaid
flowchart TD
  Intent["Intent ledger"] --> Spec["Accepted executable spec"]
  Spec --> IR["Typed semantic IR"]
  IR --> Candidate["Implementation candidate"]
  IR --> Tasks["Property obligations"]
  Candidate --> Translation["Checked translation"]
  Tasks --> Evidence["Evidence checker"]
  Translation --> Evidence
  Evidence --> Runtime["Bound artifact execution"]
  Runtime --> Trace["Observable trace"]
  Trace --> Evidence
~~~

The spec and candidate are distinct artifacts even when initially identical. Code generation must never rewrite the accepted specification as a side effect of checking code.

## Planned Rust workspace

| Crate | Responsibility | Trust position |
|---|---|---|
| foundation-types | IDs, versioned records and canonical encoding | Artifact-binding implementation |
| foundation-semantics | Typed IR and reference transition semantics | Must be mechanized or independently validated |
| foundation-obligations | Property/translation obligation construction | Soundness obligation |
| foundation-evidence | Certificate dispatch, manifests and graph validation | Acceptance boundary |
| foundation-intent | Requirement ledger, controlled-language templates and traceability | Untrusted suggestions; accepted interpretation explicit |
| foundation-frontend-resilient | Typed Resilient extraction and diagnostics | Source-to-IR obligation |
| foundation-backend-smt | Restricted VC route and model decoding | Producer; evidence determines trust |
| foundation-backend-finite | Finite graph analysis and source witness replay | Complete-model or bounded claim |
| foundation-backend-quant | Finite DTMC/MDP and exact/interval guarantees | Later supported fragment |
| foundation-translation | IR/bytecode/Rust/native validation interfaces | Evidence-producing route |
| foundation-runtime | Capability/effect execution and observation hooks | Runtime/OS/hardware assumptions recorded |
| foundation-eval | Immutable task runner, aggregation and performance profiles | Independent evaluator |
| foundation-cli | Human/agent interface, structured results | No authority to upgrade evidence |

No placeholder Cargo workspace is shipped to imply that these crates are implemented. Dependency versions and toolchain pins are selected when each route is implemented and measured.

## Transactional pipeline

1. Ingest raw request and record source/provenance.
2. Propose atomic requirements, ambiguities and assumptions.
3. Resolve interpretation through an accepted template, prior policy or explicit decision.
4. Lock requirement/spec/profile identities.
5. Generate a candidate and search for evidence under a declared budget.
6. Validate required obligations, witnesses and translation artifacts.
7. Apply the execution policy to the result vector.
8. Run the bound executable only within the authorized capability context.

Changing a locked artifact creates a new identity and invalidates dependent acceptance. Resource exhaustion returns a result; it does not relax the policy.

## Storage and cache

Artifacts are content-addressed. The cache key includes semantic and observation profile, requirement/spec/source hashes, encoder/checker/backend versions, theorem dependencies, bounds, assumptions, target and compiler flags. An LLM response cache is separate from a checked-evidence cache.

Offline checking consumes a complete bundle. Any unrecorded external dependency makes the bundle incomplete rather than verified.
