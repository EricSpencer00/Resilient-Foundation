# Typed semantic core

## Core model

A program is a typed transition system over state, environment inputs and labeled observations. The initial profile is scalar and finite under explicit bounds. Later profiles add structured values and effects without changing the meaning of existing profile IDs.

State includes locals, program counter/control context, error/outcome, input epoch, snapshot/persistent state when enabled, and counters needed by the declared property. A transition label identifies input reads, internal steps, external commands, reset/restore, commit, error, and optional time/energy charges.

## Arithmetic profile scalar-wrapping-v1

| Operation | Defined meaning |
|---|---|
| i64 representation | Signed two's-complement value of 64 bits |
| add/sub/mul | Modulo 2^64, reinterpreted as signed i64 |
| comparisons | Signed comparison; no mixed-type coercion |
| division | Truncation toward zero; divisor zero yields DivideByZero; MIN/-1 wraps to MIN |
| boolean operators | Explicit typed bool operations; short-circuit evaluation is modeled |
| errors | Observable typed outcome, not undefined behavior or an implicit panic |

Division and error order must be preserved in lowering. Rust's plain overflow behavior varies with build profile; native codegen uses explicit wrapping operations and explicit error branches. Mathematical integers are available only in a separate ghost domain with proved range/conversion obligations.

## IR shape

The initial expression IR has literals, variables, unary operations, binary operations and if. Types are explicit. Integers are decimal strings in JSON to prevent JavaScript/JSON-number precision loss. Variables bind through stable symbols. Later statement IR records blocks, branch conditions, loop invariants and returns.

IR is data, not executable arbitrary host-language code. A backend cannot reinterpret an unknown node as a no-op. Type, symbol, totality and supported-fragment checking precede task construction.

## Observation profiles

An observation projection states which values, errors, actions, ordering, time, energy and termination are visible. It may hide internal steps but must preserve all observations used by a requested property. A temporal or side-channel property cannot borrow a projection that hides its critical signal.

The scalar profile observes return value/error and termination. Recovery profiles add external action order and commit/error state. Timed profiles explicitly observe clocks/costs.

## Canonical identity

Canonical JSON is the project's documented restricted encoding: sorted ASCII property keys, UTF-8, no duplicate keys, no non-finite numbers, integers as strings where precision matters, and exact bytes for source artifacts. Hashes use SHA-256 with a type/version domain prefix. It is not described as RFC 8785 until a conforming implementation and cases exist.

Pretty-print differences do not change canonical IR identity; source identity and source maps are independently retained. Source-to-IR binding cannot be established by content hashes alone.

## Proof obligations

Typing preservation, progress/error completeness, interpreter consistency, expression/statement lowering preservation, supported-fragment completeness, observation preservation and deterministic evaluation for the exact scalar profile. Their actual theorems/checkers are planned work, not supplied by these schemas.
