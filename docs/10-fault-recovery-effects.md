# Faults, recovery and observable effects

## First fault model

Single execution thread, bounded scalar control, explicit snapshot/persistence scope, and reset/retry at declared VM/source boundaries. Specify a maximum fault count or an uninterrupted-progress assumption. AST statement boundaries are not automatically all machine-instruction or torn-write boundaries.

The environment identifies which state survives reset, whether inputs are stable within an epoch, and whether an external device has persistent deduplication state. Arbitrary silent corruption and concurrent environment mutation require different models.

## Real recovery obligation

~~~text
Init(s0) and ReachPrefix_i(s0,s)
and Fault_F(s,sf) and Recover(sf,sr)
and not RecoveryPost(sr)
~~~

Safety requires this to be unsatisfiable for every covered reachable boundary. Progress/termination and effect equivalence are separate obligations. ReachPrefix includes actual assignments, branch conditions and loop states.

## Effect discipline

| Effect | Retry behavior | Needed contract |
|---|---|---|
| Pure/local replayable work | Repeat with no external observation | Local-state and determinism relation |
| Epoch input read | Reuse/freeze or explicitly reread | Input epoch semantics |
| Idempotent external command | Repeated command has one allowed observation | Verified device/protocol idempotence |
| Deduplicated command | Use persistent request identity | Durable dedupe/ack/reset model |
| Non-replayable physical action | Retry may duplicate action | Reject retry or require an explicit transactional device protocol |

A function name, seen-field naming pattern or call named dedupe is not a semantic idempotency proof.

## External exactly-once boundary

A reset after an external action but before acknowledgement creates uncertainty. Local rollback alone cannot remove the action. At-most-once safety, at-least-once progress and exactly-once observation are different contracts. The last requires suitable environment/protocol assumptions.

## Observable recovery relation

Hide only internal retries. Compare externally visible commands, results, error/degradation signals and declared cost/time observations against an abstract transaction specification. Recovery that restores a scalar but repeats an unsafe actuator command must fail the effect obligation.

## Required cases

Wrong snapshot scope; fault after state mutation; fault before/after effect/ack; unstable sensor input; duplicate request; persistent dedupe loss; fault-budget exhaustion; recovery nontermination; retry cost overruns. Cases have independent expected traces, not just outcomes from the recovery encoder.

Leto, Perennial, Alpaca, Coati and intermittent-computing foundations are direct baselines. The research claim must name an additional source/compiler/effect/evidence guarantee.
