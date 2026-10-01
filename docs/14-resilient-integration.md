# Resilient integration and existing gaps

Source review anchor: EricSpencer00/Resilient main commit **53a9f198013655e6ad9372f8aaf463d22ee6c032**, checked 30 September 2026. These are selected source observations, not an executed end-to-end audit.

## Ownership

Resilient is the owner's language project and first evaluation frontend. Foundation extracts shared semantics/evidence functionality where there is a concrete boundary. It does not copy/fork the whole compiler or change Resilient's repository during this specification task.

## Specific integration work

| Existing surface | Observed issue | Required work package |
|---|---|---|
| recovers_to_bmc.rs | Prefix ID changes a comment; obligations do not model reachable prefix/fault/recovery state | WP-09 |
| Lean expression semantics vs embedded values | Mathematical Int vs wrapping i64; generated theorem concerns the lowered body | WP-03, WP-05, WP-12 |
| probabilistic_contracts.rs | Declaration checks and empirical trial accounting | WP-17 |
| power_contracts.rs / wcet_contracts.rs | Initial AST/fixed-loop cost assumptions | WP-16 |
| semantic_regression.rs | Clause counts/failure variants, not logical compatibility | WP-19 |
| idempotent_handler.rs | Naming/access heuristic | WP-10 |
| transaction_commit.rs | Local commit/rollback discipline distinct from external effect semantics | WP-10 |
| tla_refines.rs | Mapping metadata; action/proof discovery deferred | WP-15 |
| contract_certificate.rs | Useful result/query/signature artifacts; source-to-query trust remains | WP-07 |

## Current embedded status

EMBEDDED_PIPELINE's current heading reports scalar source -> bytecode -> embedded-loader/QEMU execution. Older paragraphs describe the historical missing path. Do not treat those historical paragraphs as the current status. This review did not rerun the CI result.

## Incremental adoption

1. Export a versioned typed scalar model without altering default source behavior.
2. Compare exact arithmetic/errors against Foundation's profile.
3. Introduce strict proof-status output alongside existing diagnostics.
4. Implement reachable-state recovery obligations and independent replay.
5. Connect certificates to source/model/target identities.
6. Enable a supported exactness claim only after its required checks exist.

Foundation policies can require stronger evidence than current Resilient compilation. That policy must not retroactively claim the current compiler provides the new guarantee.

## Validation and upstream work

Implementation in Resilient follows its own AGENTS.md, public-interface tests and evidence workflow. Preserve user authorization boundaries for that repository's changes. This new repository holds the specification and planned integration work; it does not make or push an upstream code change.
