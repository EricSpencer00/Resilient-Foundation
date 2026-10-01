# CI and release gates

## Current repository gate

The specification validator checks schemas, linked documents, requirement/work-package coverage and dependency cycles, artifact identities, example invariants, evaluation formulas/profiles and deliberately invalid result manifests. It is read-only except its local validation report when requested. It does not call models or solvers.

A successful specification job establishes consistency only. The scalar implementation and end-to-end jobs check their declared supported fragment under the recorded trust assumptions.

## Future gates by scope

| Change | Required gate |
|---|---|
| Lexer/parser/types/profile | Independent conformance boundaries and profile identity checks |
| VC/model encoder | Valid/invalid matched oracle cases and encoding soundness evidence |
| Evidence checker | Forged/stale/cyclic/unsupported evidence rejected; supported certificates checked |
| Codegen/optimization | Source-target relation and differential cases; correct target binding |
| Recovery/effects | Reachable-prefix and external reset/ack traces |
| Quantitative route | Exact/interval numeric oracle cases and joint-event semantics |
| Model adapter | Fixed task protocol, no leaked/altered oracle, reproducible serving manifest |
| Performance change | Matched fixed-artifact measurements and no soundness regression |

## Cadence specification

Per change: affected deterministic conformance/negative evidence checks.
Nightly, once infrastructure exists: fixed artifact corpus and extended fault/translation cases.
Per package release: full supported-fragment gates and matched performance run.
Per selected model release: versioned smoke/screen/full model evaluations with an explicitly approved compute/spending budget.

This describes desired CI behavior. It does not create recurring jobs or spend API credits now.

## Release declaration

Each release lists implemented capabilities, supported tuple/profile, required/achieved evidence, unresolved assumptions, task counts/coverage, empirical results and actual hardware/toolchain. No milestone is complete from a checkmark in a roadmap file alone.

## Failure behavior

Do not overwrite an accepted artifact with a failed build. Keep rejected candidate evidence inspectable. Unknown/Inconclusive remains visible and cannot be bypassed through default success or optional-warning treatment in a strict policy.

## Implemented scalar boundary

`make check` now includes Rust debug/release conformance, parser/wire/target-reader tests, formatting, lint and recorded-report integrity. `make e2e` invokes actual Z3 and Rust, requires zero skipped tests and saves host/tool/source/evidence identities plus oracle executions and a replayed counterexample. CI defines an Ubuntu scalar end-to-end job with observed identities recorded in each run; no hosted run is claimed until observed. The saved NUC report is experimental conformance evidence, distinct from schema consistency, kernel evidence and native equivalence.
