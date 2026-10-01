# One task through the entire pipeline

## Accepted request

"For an integer x, return x if x is nonnegative, and return zero otherwise."

The illustrative requirement ledger selects all signed i64 inputs, no external effects, exact equality to an executable if-expression, and return/error/termination observations. No arithmetic overflow occurs in this example; it is useful for branch/domain checks.

## Artifacts

examples/nonnegative/ contains the request, requirement ledger, accepted executable IR, candidate IR, semantic profile reference, obligation plan, open evidence graph and illustrative result. None claims that a solver, proof kernel or native validator ran.

The source sketch uses proposed Resilient profile syntax and is labeled .rz.example. It is not a claim of today's parser support.

## Independent expected cases

MIN -> 0; -1 -> 0; 0 -> 0; 1 -> 1; MAX -> MAX. Invalid results include -1 -> -1, 0 -> 1 and MAX -> 0. A mutant that changes >= to > is observationally equivalent for this specific function; do not count it as an invalid mutant. A mutant returning x+1 for nonnegative x is invalid, including overflow cases.

This equivalent-mutant detail matters: rejecting every textual difference is not semantic verification.

## Required obligations

Typing; complete/all-i64 input domain; deterministic total evaluation; candidate/spec equality; correct error/termination observations; supported lowering relation; source map; actual artifact binding; chosen execution-policy evidence.

## Translation example

The intended Rust expression is if x >= 0 { x } else { 0 }. An emitter witness must bind the actual source/IR and generated function. A runtime test of the five examples is empirical validation; a formal all-input equality proof is separate; a native-code relation is separate again.

## Recovery extension

A later task updates persistent state and emits a deduplicated external command. Its model includes a fault after the action/before acknowledgement. Expected observation is determined by the accepted device protocol, not by simply restoring local variables. This extension cannot reuse the pure scalar certificate as a recovery proof.

## Result interpretation

The current example has intent accepted as an illustrative design decision, formal/translation results Unknown, runtime NotRun and no checked acceptance. Its expected manifest rejection under a strict exact/native policy is intentional.
