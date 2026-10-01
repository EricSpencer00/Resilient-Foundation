# Research positioning and inspiration

## ProofTree

The working interpretation of "prooftree" is [prooftree.ai](https://www.prooftree.ai/). Its public preview describes a verified mathematics workspace and persistent human/AI reasoning. The inspiration is evidence tied to reusable work and an inspectable proof graph. Its private code and guarantees were not audited; no claim of its spec-to-code implementation is made.

The older Proof General/Coq proof-tree viewers are a separate line of tooling. The term alone does not identify a compiler proof architecture.

## Direct adjacent work

| Area | Baselines | Proposed distinction to investigate |
|---|---|---|
| Intent-aligned formalization | FRET, VeriSpecGen, Verus-SpecGym | Accepted controlled-language interpretation tied to the same execution/evidence model |
| AI program/proof generation | AlphaVerus, Verina, vericoding, Vero | Model-agnostic source-to-target/effect obligations and transparent denominators |
| Rust verification | Verus, Creusot, Aeneas | Specific Resilient/reset/effect/target connection |
| Evidence workflow | ProofTree, Subak, CoVeriTeam | Precise semantic translation/evidence contracts, not a generic graph |
| Fault/recovery | Leto, Perennial, Alpaca, Coati | Defined embedded source/bytecode/runtime preservation with effects |
| Quantitative analysis | ETAP, Rely, Caesar/HeyVL, PRISM/Storm | Specific joint event over that same checked execution model |
| Verified compilation | CakeML, verified Dafny, Low*, WaveCert | Restricted fault/effect/resource extension or target validation method |

These rows describe overlap, not unoccupied fields. Subak's documented proof-tree/validation workflow is especially relevant product prior art; its presence prevents claiming a generic evidence graph is new.

## Provisional research hypothesis

A bounded Rust-familiar embedded fragment can carry compiler-checked recovery/effect contracts and source-linked, independently checkable translation evidence, with later joint timing/energy/reliability guarantees. Novelty of that precise combination remains unestablished.

## What to compare

Task/domain; accepted fragment; faults and persistent state; external observation; totality/fairness; source-to-model evidence; target/compiler trust; certificate checking; workload cost and coverage. A baseline's failure must not be caused by intentionally mismatched assumptions or missing adapter engineering.

## Claims to avoid

First formal AI programming language; first proof graph; all prose translated exactly; all Rust programs compiled with proof; no compiler/runtime trust; universal support for all properties; signed certificate equals soundness; tests passing equals intent faithfulness.

## Research artifacts

Source/pinned prior-art references are in research/references.md and research/resilient-source-review.json. Imported prior-art catalogs retain their review-depth labels; they are source entries, not counts of unique independently audited systems.
