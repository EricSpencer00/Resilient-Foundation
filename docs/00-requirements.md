# Requirements and product boundary

## Mission

Let an AI produce fast, useful software in a Rust-familiar language while a deterministic verification pipeline checks the declared behavior and the translations used to realize it. Resilient is the first language frontend. Foundation is the shared semantic/property/evidence infrastructure, not another competing language.

The long-term platform serves agent orchestration, application logic and selected systems/embedded workloads. Neural inference may be executed through a typed component interface. Proving a caller's capability discipline does not prove a neural model's answer is true or its learned behavior is safe in all environments.

## Required user outcomes

- A requirement can be traced to its formal clause, implementation component, proof obligation and actual deployed artifact.
- A complete executable spec can be compiled through checked translations with an exact observable-behavior claim.
- A general relational contract can be implemented with an explicitly labeled refinement claim.
- A counterexample identifies source locations and the assumptions/bounds needed to reproduce it.
- A new model can use familiar code or structured tools without writing TLA+, SMT-LIB or Lean for ordinary tasks.
- A new backend can advertise exactly the supported task/semantic/evidence tuple.
- A dependency or spec update invalidates affected evidence and preserves unaffected evidence under a checked dependency relation.
- Verification and native execution costs are measured independently.

## Mandatory boundaries

The platform MUST NOT certify the meaning of arbitrary prose merely because an LLM generated a plausible specification. It MUST NOT confuse schema validity, successful compilation, passing tests, model satisfaction, solver success, kernel proof, translation validation or production-environment assumptions.

A safety claim includes the input domain, machine arithmetic, errors, observation projection, scheduling/fault assumptions and any horizon. General program equivalence and arbitrary termination are undecidable; supported fragments and Unknown are fundamental API results.

The exact normative commitments are enumerated in requirements/registry.json and linked to milestone acceptance work. A capability cannot be released merely because its annotation or command exists.

## Success criteria for the first slice

One deterministic scalar spec, one candidate implementation, one independently checked source-level obligation, one validated lowering, one explicit native/toolchain trust boundary and one source-linked result. A real wrong arithmetic or wrong branch must be rejected.

## Nonfunctional goals

Rust-native implementation, reproducible artifacts, low-cost proof replay, explicit caching, stable machine-readable interfaces and measured runtime parity with safe Rust on matched tasks. These are goals with evaluation gates, not existing performance claims.
