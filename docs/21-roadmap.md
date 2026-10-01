# Implementation roadmap

Milestones are dependency gates, not calendar estimates. Implementation begins with independent counterexamples and exact semantics; broad integrations follow successful evidence.

| Milestone | Scope | Exit condition |
|---|---|---|
| M0 Specification | Normative docs, shapes, requirements, illustrative cases, eval protocol | Specification validator passes; no implemented compiler/proof claim |
| M1 Scalar semantics | Typed scalar IR/reference semantics and Resilient extraction | Boundary/error/branch cases, supported-fragment rejection and binding work |
| M2 Formal evidence | Restricted equivalence/safety obligations and actual proof/witness checking | Valid/invalid pairs, no known false acceptance, explicit solver/kernel classes |
| M3 Checked lowering | IR/bytecode/Rust relation and runtime-source connection | Deliberately wrong arithmetic/lowering rejected; remaining native trust disclosed |
| M4 Recovery/effects | Reachable reset states, snapshots, input epochs and external protocol | Fault-position distinctions, unsafe retry rejected, progress assumptions visible |
| M5 Native artifact | Restricted target semantics and machine-code/verified-backend route | Artifact-specific relation checked; stronger native claim available only here |
| M6 Quantitative/relational | Joint resource probability, two-trace tasks and model completeness | Independent numerical/relational cases and extraction evidence |
| M7 Agent/repository product | Typed execution capsules, Rust adapters, incremental updates | Useful original repository tasks; model/package/runtime lanes measured separately |

Some work packages in M6/M7 can be prototyped earlier with lower assurance, but cannot inherit a later milestone's guarantee.

## Immediate work

WP-03 -> WP-04 -> WP-05 -> WP-06 -> WP-07 -> WP-08.
The first meaningful program is the scalar example, with all-i64 behavior and incorrect-boundary mutants. Recovery then follows WP-09/WP-10.

## Requirements for a contribution claim

A new theorem/method/accepted fragment/evidence guarantee, or a reproducible practical improvement over the nearest baseline. Pin identical task/domain/fault/effect assumptions. Rust implementation and feature aggregation alone do not establish academic novelty.

## Stop conditions

An unsupported language feature, failed encoder/translation relation, missing certificate support or model ambiguity blocks the stronger claim. The project may still expose useful diagnostics at a disclosed lower assurance. It must not rename that lower class as exactness.

## Planning ownership

Work packages have dependencies, required artifacts, independent acceptance cases, linked requirements and planned status in roadmap/work-packages.json. Assign owners and estimate time after M1 establishes real complexity. Do not promise universal proof automation or every target/backend in the first release.
