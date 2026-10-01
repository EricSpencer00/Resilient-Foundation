# Language and supported profiles

## Relationship to Resilient and Rust

The surface remains Resilient with Rust-familiar functions, types, enums, blocks and explicit effect boundaries. Ordinary users and LLMs write source or structured AST edits; advanced backend languages are optional interfaces.

This document proposes a verification profile, not a replacement implementation of Resilient's current grammar. Unsupported current language features remain usable outside a claimed verified profile only when the execution policy permits that lower assurance.

## Initial scalar profile

Supported: i64, bool, pure total scalar functions, let/assignment, typed conditions, return/error outcomes, wrapping add/sub/mul, defined division and comparisons, bounded loops with explicit invariants/termination obligations, and acyclic calls after scalar expressions are proven.

Initial slice M1 may start with expressions and if; milestone declarations enumerate enabled operations. Arrays, heap, pointers, float, async, concurrency and FFI are not silently approximated.

Illustrative surface:

~~~rust
// Proposed profile syntax; not asserted to compile in today's Resilient.
profile scalar_wrapping_v1;

spec fn nonnegative(x: i64) -> i64 {
    if x >= 0 { x } else { 0 }
}

fn nonnegative_impl(x: i64) -> i64
    implements_exactly nonnegative
{
    if x >= 0 { x } else { 0 }
}
~~~

## Contract forms

- requires / ensures: input/output predicates with errors and frame/effect conditions where relevant.
- implements_exactly: a complete executable spec and explicit observation relation.
- refines: a permitted-behavior contract, including declared nondeterministic choices.
- invariant / decreases / bound: distinct safety, termination and analysis-scope obligations.
- recovers_to: post-fault recovery relation plus progress conditions.
- effect capability: authorized calls and observable effect protocol.
- resource / probability / relational clauses: typed tasks, not free quoted strings interpreted differently by each backend.

The names above are design vocabulary. Syntax must be reconciled with the existing parser when the corresponding milestone is implemented.

## Ghost code

Ghost/spec/proof terms cannot affect executable results or leak secrets through runtime behavior. Erasure has its own preservation obligation. No assume, axiom, external-body or trusted-FFI mechanism can disappear from the evidence manifest.

## Language expansion rule

A feature enters a verified profile only with typing, operational semantics, encoder/codegen obligations, error/fault interactions, conformance cases and an accepted evidence route. Parsing a feature is insufficient.

## LLM ergonomics hypothesis

Rust familiarity should reduce the entry cost for common models, but verified Rust may still be harder than higher-level verification languages. Measure paired tasks across Rust/Resilient, Verus and Dafny/Lean under matched requirements and budgets. Familiarity and native speed are design motivations, not benchmark findings.
