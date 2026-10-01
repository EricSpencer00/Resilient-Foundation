# End-to-end scalar goal

Owner: native Codex goal in chat `01a0f563-909f-78b1-9105-bf9f167ce4cc`. Started 1 October 2026. Baseline: `728fcf9`; frozen independent oracle: `examples/nonnegative/oracle.json`. The existing illustrative example remains illustrative.

## Acceptance gate

Deliver a usable scalar CLI path from a versioned controlled requirement and an LLM-authored candidate in the supported Resilient fragment to typed IR, all-input equivalence checking, replayed counterexamples, bound evidence, checked Rust translation and guarded native execution. Positive cases must execute with matching observations. Wrong branches/arithmetic, malformed input, unsupported constructs, absent/unknown solvers, stale/forged evidence and altered target artifacts must fail at the correct boundary. A semantically equivalent candidate must remain accepted.

The initial execution policy explicitly trusts parsing/encoding, the tested Rust reference runtime, rustc/LLVM, OS and hardware. It does not claim kernel-checked proofs or machine-code equivalence. `strict_native_exact` must stay unsupported until its missing native relation is implemented.

## Implementation frontier

1. Strict wire loader, canonical identity and a restricted source frontend with source maps.
2. Bit-vector equivalence via the existing Z3 executable; observations include typed errors and short circuiting. Independently replay every returned witness through the Rust reference runtime.
3. Reconstruct obligations from bound inputs during evidence checking; do not trust producer status or a producer-supplied query.
4. Emit a restricted Rust representation using the reference runtime, independently decode the representation and check its all-input relation. Bind toolchain, target and exact executable bytes.
5. Require the evidence check before native execution. Rebuild and compare native bytes at the prototype trust boundary, then compare concrete execution observations with reference evaluation.
6. Freeze the assistant-authored candidate, add CLI conformance cases, run on the NUC, retain evidence and focused commits.

Verus/AutoVerus remains a later Rust proof-generation adapter. Installing a larger verifier before the scalar acceptance boundary works would not establish these missing links.

## Execution and limits

Personal private project. Editing and lightweight verification stay on the MacBook. Substantial compilation and solver suites run on `hst-bench` through the MacBook's canonical ProxyJump route. No user token or spending limit was supplied; prefer existing free capacity and bounded subprocess budgets. Do not start model servers on the MacBook or send private inputs to new external model services.

Observed NUC tools: `/usr/bin/z3` 4.8.12, Python 3.12.3 with pinned jsonschema 4.25.1, and Rust 1.98.1 through `/home/eric/.cargo/bin/cargo` and `/home/eric/.cargo/bin/rustc`. The task-owned workspace `/tmp/resilient-foundation-goal-130N7I` held compilation and solver artifacts. Its final evidence was retained locally and integrity-checked, then the entire task-created workspace was removed and absence confirmed. Temporary Mac transfer metadata in that copy was removed before the repository gate. No agents, model servers, unattended jobs, paid resources, external model calls or upstream repository changes were created. The authoritative checkout and this branch are retained; no branch was pushed or published.

## Outcome

The first supported scalar end-to-end acceptance gate passed on 1 October 2026. The CLI accepts the locked controlled requirement and Codex-authored candidate, checks all declared inputs with actual Z3, validates the restricted Rust constructor relation, reconstructs evidence independently and executes bound native bytes with matching reference observations. A wrong branch returns a validated Rust-replayed counterexample. Equivalent boundary syntax remains accepted.

The retained `validation/e2e.json` records 36 conformance tests, zero failures/skips, five frozen oracle executions, 50 in-process real solver invocations, three deliberate fault-solver invocations and 37 native compilations. CLI subprocess calls are additional and excluded from those counters. Source, test, driver, tool and evidence digests bind the run. Oracle SHA256 remains `353683fa08bc2e60c2fd5eeea2e0ce5a17572892bdfff7c621595941f9de640e`.

The broader `make check` gate passed: specification and recorded-evidence integrity, all 14 Rust conformance tests in both debug and release, eight validator policy tests, 13 lightweight Python tests, Rust formatting and lint. The 23 solver/native tests are explicitly skipped in that lightweight lane and all execute in the required 36-test end-to-end lane. The MacBook reran only lightweight checks and evidence integrity after collection. CI configuration exists; no hosted run is claimed.

Reproduction on the compute host used the pinned requirements, then `FOUNDATION_CARGO=/home/eric/.cargo/bin/cargo FOUNDATION_RUSTC=/home/eric/.cargo/bin/rustc .venv/bin/python scripts/run_e2e.py --solver /usr/bin/z3`, followed by `make check`. Build/check/run commands and supported syntax are documented in `docs/23-api-cli.md` and the README.

The delivered route is experimental and restricted to one controlled requirement template and pure scalar source. It trusts extraction/encoding, Z3, the tested reference evaluator, Rust compilation, OS and hardware. No kernel proof, arbitrary Rust verification, native-machine equivalence, stateful recovery, performance/model benchmark or general full-stack formal verification claim is made. Those remain separate roadmap acceptance gates. This goal closes the first supported route; it does not promote the larger work packages to complete.
