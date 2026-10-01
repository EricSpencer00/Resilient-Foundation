# Property and backend task model

## Task tuple

Every route receives (program fragment, semantic profile, environment/fault model, observation projection, property, quantifiers, bounds, evidence requirement). Backend selection must match the entire tuple. A solver name alone is not a capability declaration.

## Property catalog

| Family | Representative query | Required distinction |
|---|---|---|
| Functional/safety | All admissible executions satisfy a postcondition/invariant | Partial vs total correctness |
| Existential reachability | Some reachable state/trace reaches goal G | Witness vs proof of absence |
| Temporal | Always/eventually/until under declared fairness | Infinite traces vs finite/bounded approximations |
| Branching/game | Exists strategy, all adversaries, nested state/path queries | Controller policy vs merely favorable trace |
| Graph/meta-analysis | SCC, deadlock, path uniqueness under a defined path notion | Finite graph completeness, simple paths vs walks, stuttering |
| Relational/hyper | Compare two or more executions under input/secret alignment | Quantifier prefix, alignment and observation |
| Probabilistic | Min/max probability or expected reward | Distribution, nondeterminism and scheduler class |
| Statistical | Empirical inference under a sampling procedure | Confidence procedure vs logical theorem |
| Recovery/resource | Post-fault safety, progress and accumulated costs | Fault budget, retries, external effects |
| Regression | New implementation preserves old client guarantees | Pre/post/effect/failure/resource relations |

## Initial routes

Restricted exact bit-vector scalar equivalence and safety first. Finite complete exploration and source witness replay follow. Initial relational support is bounded two-trace universal checking under explicit alignment. Quantifier alternation, general HyperCTL*, infinite-state games and arbitrary probabilistic programs are not promised by that support.

Future adapters may use SAT/SMT, Stateright, TLC/Apalache, PRISM/Storm, Caesar/HeyVL and proof assistants. Backends are reused where their semantics fit. They are not installed or reimplemented merely to populate a feature list.

## Correct TLA+ interpretation

TLA+ specifications describe allowed behaviors. TLC can find a reachable-state witness by exhibiting a counterexample to an invariant that excludes the goal. That practical route differs from a native existential path modality and does not solve arbitrary hyperproperty/model-wide analysis. Self-composition/history variables have defined uses and proof conditions; their presence is not automatically a refinement failure.

Foundation provides explicit task kinds rather than pretending every query is one TLA+ invariant.

## Bounds and negative results

A found reachability witness is validated against the concrete source fragment. A bounded failure to find a witness is not an unbounded absence theorem. Finite complete graph analysis requires justified state closure/completeness. A uniqueness query states whether it counts simple paths, schedules, observable traces or walks.

## Evidence classes

A raw SAT/UNSAT result is solver-checked evidence. A validated counterexample/witness is distinct from an independently checked UNSAT proof. A proof certificate must be supported by the checker for the exact theory/format used. Unsupported theories, solver Unknown, missing solver and numeric nonconvergence do not become success.

## Numeric semantics

Probabilities/rewards use exact rationals or rigorously bounded intervals on finite models. Floating point estimates, approximate statistical results and conservative analytic bounds carry separate classes and assumptions.

## Implemented scalar boundary

The experimental `scalar-smt` route implements all-input equivalence for pure i64/bool expressions using QF_BV, including wrapping arithmetic, signed division and observable divide-by-zero errors. SAT counterexamples are replayed through the Rust reference evaluator. Unknown, timeout and missing solver remain distinct failures. Public build locks one controlled nonnegative requirement template; safety/refinement, stateful models and other backend families remain planned.
