# Rust, formal methods and LLM routes

Primary documentation reviewed 30 September 2026. This is an integration decision, not an executed verifier comparison or a benchmark result. "Other Rust verification package" was interpreted as the Rust verifier ecosystem; no separate Rust verifier repository was found in EricSpencer00's accessible repository list.

## Decision

Keep Foundation's first scalar route bit-precise and small. Use Verus as the first Rust functional-verification comparison, with AutoVerus and VeruSAGE as candidate proof-generation baselines once a real checker and artifact binding exist. Preserve the existing milestone order: reference semantics, source extraction, formal checking, checked evidence, translation and runtime composition. This recommendation follows the supported fragments and available primary implementations; it has not been established by a performance experiment.

## Comparison

| Route | What it contributes | Foundation role and limit |
|---|---|---|
| [Verus](https://github.com/verus-lang/verus) | Specifications, proof code and executable code for a supported Rust subset, checked with automated solvers | First Rust functional-verification route to evaluate. Record assumptions and trusted specifications; Rust/native compilation remains a separate boundary. |
| [AutoVerus / VeruSAGE](https://github.com/microsoft/verus-proof-synthesis) | LLM-generated proof candidates and verifier-guided repair for algorithmic and systems code | Generation baselines around Verus. They do not replace the checker, validate unstated intent or establish native translation correctness. |
| [Kani](https://github.com/model-checking/kani) | Bit-precise Rust model checking and nondeterministic harness inputs | Candidate independent arithmetic/error checker. Preserve harness constraints, reachability and analysis bounds. |
| [Creusot](https://github.com/creusot-rs/creusot) | Deductive Rust verification through Coma and Why3 | Alternative Rust route for annotated contracts; adds its own translation, tooling and prover boundary. |
| [Aeneas](https://github.com/AeneasVerif/aeneas) | Safe Rust functionalization through Charon/LLBC into proof-assistant backends | Candidate kernel-facing semantic route. Unsupported features and external models remain explicit; it is not a blanket machine-code proof. |

Verus separates [spec, proof and executable modes](https://verus-lang.github.io/verus/guide/modes.html). Its [trust documentation](https://verus-lang.github.io/verus/guide/tcb.html) identifies `assume`, external bodies and axiomatic specifications. An adapter must inventory these mechanisms in the evidence manifest rather than treating a successful exit as an unconditional theorem.

Microsoft's [primary synthesis repository](https://github.com/microsoft/verus-proof-synthesis) distinguishes algorithm-level AutoVerus from systems-oriented VeruSAGE. Its documented benchmark setup uses different Verus revisions for the two suites: `33269ac6a0ea33a08109eefe5016c1fdd0ce9fbd` and `ddc66116aa7a844a9e19cc50922fe85c84b8b4a5`. Pin the chosen benchmark and verifier together when reproducing them. Neither system was installed or run in this setup, and no model/API key was used.

Kani's [result definitions](https://model-checking.github.io/kani/verification-results.html) distinguish success, failure, unreachable and undetermined checks. Include reachability cases to catch vacuous success, and do not turn undetermined or unsupported results into acceptance. Aeneas documents its [supported subset and limitations](https://github.com/AeneasVerif/aeneas#targeted-subset-and-current-limitations); external Rust definitions need explicit models. Creusot's [architecture](https://github.com/creusot-rs/creusot) translates to Coma/Why3, so it must have a separate capability/evidence record.

## First adapter experiment

Freeze the existing nonnegative specification and oracle. Verify the correct candidate over all i64 inputs. Reject mutants that return the input on the negative branch, change the zero result, or overflow an intermediate result near MAX. Include the oracle's equivalent `>=` to `>` mutant: both zero branches return zero, so rejecting that candidate would reveal an overly syntactic equivalence check.

Record input domain, wrapping/error semantics, exact obligation, source/model identities, verifier revision, assumptions, checker output, timeout and independently replayed counterexamples. Require a failure when the checker is absent, the profile mismatches or required evidence is missing. Keep all cases in the denominator. Tests, checked contracts, translation checks, intent validation and model cost stay separate in the result.

## Full-stack composition

The full-stack goal needs a checked chain from accepted intent to source semantics, candidate behavior, lowering and deployed execution. Each of the routes above can support part of that chain. None of the reviewed documentation establishes that installing one package closes all of those boundaries. Foundation's contribution must be the actual connected evidence and useful supported scope, measured against pinned baselines.
