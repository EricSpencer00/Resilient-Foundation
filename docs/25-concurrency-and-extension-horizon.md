# Concurrency and extension horizon

The product vision is broad; each additional semantic feature needs its own supported-fragment and evidence route.

## Concurrency

Define execution/scheduler semantics, atomicity, memory model, interference, persistence and observation. A sequential proof plus an async syntax parser does not establish concurrent correctness. Begin with an actor/message model or a verified capability-isolation fragment before general shared-memory Rust.

Fairness is a declared assumption. Existential strategy synthesis and all-schedule safety are separate tasks. A bounded interleaving exploration result is not an arbitrary infinite-schedule theorem.

## Floating point

Define IEEE format, rounding, NaN/signed-zero/infinity/error behavior and comparison semantics. Mathematical real proofs require numerical error obligations. Initial scalar exactness excludes float. Neural tensor computation can initially be an assumed/monitored external component with explicit shape/range interfaces.

## Probabilistic and learned components

A distribution is a model/assumption unless established for the component. Randomized algorithms, hardware faults and learned-model uncertainty are different sources of probability. Do not equate empirical model answer accuracy with a formal stochastic transition specification.

## Higher-level language features

Collections, heap, ownership/borrowing, modules, generics, trait resolution, macros and FFI expand the translation obligations. Safe Rust subset routes such as Verus/Aeneas may provide leverage, subject to their explicit supported features and trust assumptions.

## Other frontends

Adopt a second frontend only after one complete Resilient path is useful. Native Rust is the next practical candidate. Python/JavaScript application adapters can expose verified kernels, but do not claim whole-language equivalence without a semantics/translation route.

## Distributed systems

Specify message/network failure, crash persistence, consistency, membership, clocks and external stores. TLC/Stateright/PRISM-style models support different questions. A generated protocol model is not the implementation until extraction/refinement is justified.

## Expansion acceptance

For every feature: typing, operational/observational semantics, profile version, encoder/codegen soundness, error/fault/resource interaction, independent valid/invalid cases, evidence format and supported performance data. Unsupported remains a useful and honest result.
