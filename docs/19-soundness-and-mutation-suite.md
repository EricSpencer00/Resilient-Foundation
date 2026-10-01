# Soundness and adversarial evaluation

## Release-critical property

No known invalid claim in the required supported-fragment suite may be accepted. One reproducible false acceptance blocks the affected capability release. Zero observed false acceptance is necessary evidence; it is not a proof that no soundness bug exists.

## Independent expected results

Cases are authored from mathematical/machine semantics, trusted requirements or independently reviewed traces before running the package. The encoder cannot generate both the tested proposition and its sole expected answer.

## Case families

1. i64 overflow, MIN/-1, divide-by-zero and error-order changes.
2. Incorrect branches, signed/unsigned comparison, narrowing and JSON precision loss.
3. Strengthened preconditions, weakened postconditions and vacuous assume(false).
4. Dropped state mutation/branch guard in a recovery-prefix model.
5. External action followed by reset; lost dedupe state; unstable input epoch.
6. Termination omitted from exactness; cutoff mistaken for semantic loop bound.
7. Solver Unknown/missing solver/timeout promoted to Proved.
8. Counterexample decoding mistakes and abstraction-only witnesses.
9. Unsupported theory/IR node hidden in a helper or FFI.
10. Stale certificate after source/spec/profile/target/assumption change.
11. Evidence dependency cycle, forged proof status or test node satisfying a theorem.
12. Wrong target arithmetic, codegen optimization or source map.
13. Marginal probability multiplication and unbounded retry costs.
14. Predicate changes with equal annotation count.
15. Wrong graph path notion and fairness/strategy assumption.
16. Certificate valid for a different query/proposition.
17. Successful tests accompanied by a provably weak spec.
18. Dependency wrapper advertised as proof of the external implementation.

The catalog records scenario, independent oracle, expected rejection/result, supported milestone and reason. Catalog entries are planned benchmark tasks; they are not executed package results.

## Mutations

Create valid/invalid matched pairs. Perturb one semantic fact at a time: operator, boundary, clause, observation, state transition, hash, dependency, bound or environment assumption. Mutation score is rejected semantically relevant invalid mutants / valid generated invalid mutants. Equivalent mutants are reviewed/excluded with recorded justification.

Measure valid-program false rejection, Unknown and Unsupported separately. A checker that rejects everything has zero false acceptance but no useful completeness/coverage.

## Metamorphic checks

Alpha-renaming, independent statement reordering under a proved side condition, canonical serialization and semantics-preserving optimization should retain results. An arbitrary syntactic rearrangement is not assumed semantics-preserving.

## Current checks

The repository implements schema/manifest/traceability consistency checks and negative illustrative manifests. It does not execute the runtime, solver or machine-code mutants yet. Those become milestone acceptance evidence when the implementations exist.
