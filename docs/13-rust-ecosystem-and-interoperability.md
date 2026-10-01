# Rust ecosystem and interoperability

## Reuse strategy

Use Rust for shared data structures, compiler/runtime integration, APIs and performance-sensitive code. Prefer existing verifier and model-checker routes where the fragment and evidence fit. Standard Rust familiarity is an ergonomic goal; Rust source acceptance and formal correctness are different capabilities.

Verus supports a Rust subset with specification/proof constructs. Creusot supplies another Rust verification route. Aeneas functionalizes a supported Rust subset into proof-assistant representations. They are comparison/adaptation candidates, not interchangeable proof kernels or verified machine-code compilers.

## Library interfaces

A dependency interface records input/output, memory/effect/frame, failure, concurrency, resource and environmental contracts. The dependency is verified, assumed or empirically validated under a named route. Public Cargo metadata alone is not proof evidence.

Unsafe Rust, raw pointers, macros, panics, async, concurrency and FFI require explicit profile support. Initially reject them from exact scalar mode. A generator cannot bypass the restriction by placing behavior in a helper crate or external body.

## Data and arithmetic

Pin serialization formats and integer/error behavior across boundaries. No loss through JSON numbers, unchecked narrowing casts, float coercions or host-language defaults. Ghost mathematical arithmetic converts to machine values only through validated conditions.

## Native execution

Use explicit wrapping/checked operations as required by the profile. Initial rustc/LLVM compilation is an explicit trusted boundary. A later native validation route proves a specific artifact relation for a restricted target fragment. It must not inherit a blanket assurance from Rust's type system.

## Targets

Start with one host target and one restricted scalar route. Embedded no_std and WebAssembly are subsequent profiles with their own loader/runtime/cost assumptions. Portable source syntax is not automatically portable evidence.

## Cargo experience

Planned: cargo-compatible invocation, ordinary diagnostics, source spans, editor/tooling support, lockfile-based build identity and machine-readable verifier results. Installation should be modular; a scalar user need not install TLA+, probabilistic engines and interactive provers.
