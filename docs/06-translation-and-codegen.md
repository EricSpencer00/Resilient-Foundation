# Translation, compilation and code generation

## Checked edges

| Edge | Needed obligation | Initial route |
|---|---|---|
| Source -> typed IR | Parsing, name/type resolution and semantic preservation | Restricted frontend plus independent conformance/witness validation |
| Spec IR -> candidate IR | Exact equivalence or declared refinement | Restricted bit-vector obligations; termination/error/effects included |
| IR -> bytecode | Simulation preserving chosen observations | Per-artifact translation validation, then mechanized rules |
| IR -> Rust source | Expression/control/effect preservation | Restricted emitter plus validation against typed IR |
| Rust/bytecode -> native artifact | Target semantics and toolchain relation | Explicit trusted-toolchain profile first; native translation validation later |
| Artifact -> deployed execution | Binding, loader/runtime/environment assumptions | Hash-bound execution and declared platform model |

A chain fails if any required edge is missing. Kernel-checking a program theorem does not prove the compiler is correct.

## Two compilation routes

1. **Bytecode/reference route:** a small instruction set whose semantics is connected to IR. A theorem about VM source remains conditional on compiling/running the VM correctly. This route simplifies controlled reset boundaries and fault replay.
2. **Native Rust route:** generate a restricted Rust function/module and use rustc/LLVM. Early releases disclose trust in this compilation boundary. The final native-exact claim requires a checked per-artifact machine-code relation or a verified backend for the selected target fragment.

Rust-native performance is desirable; the design must not label ordinary rustc compilation as a verified compiler.

## Native validation horizon

Begin with scalar leaf functions on a pinned architecture/ABI, explicit wrapping arithmetic and no heap/FFI. Lift emitted machine instructions into a defined target model, compare against the IR function, check memory/ABI/error behavior, and validate the returned evidence. Expand only with a supported-instruction and trust declaration.

This is a research/implementation project, not a claim that arbitrary optimized Rust binaries are already verifiable. If the artifact cannot be lifted or the validator times out, return Unsupported/Unknown and withhold the stronger native claim.

## Optimization rule

Optimization cannot weaken preconditions, change error order, drop observations, assume mathematical arithmetic, elide checked capability effects, or turn a bounded proof into an unbounded one. Translation evidence binds optimization flags and exact target bytes.

## Counterexample validation

A model from a comparison solver is replayed through source/IR and target semantics. A mismatch in decoding, abstraction or unsupported behavior returns InvalidEvidence. The replay artifact contains inputs, intermediate relevant states and observations.

## Independent checks

Use separately authored boundary examples and differential execution across reference semantics, bytecode VM and generated Rust. Differential agreement is empirical evidence; all three implementations may share a bug. Formal preservation or a checked translation artifact is a distinct release gate.

## Build identity

Record source, canonical spec/IR, compiler/emitter/checker/backend versions, dependency digests, target triple, ABI, optimization flags, enabled features, error/overflow policy and target artifact hash. An accepted result for one build does not cover a differently compiled binary.
