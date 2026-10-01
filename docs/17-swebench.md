# SWE-bench integration

## Use the original task correctly

Pin dataset revision, instance ID, pre-patch repo commit, official harness commit, container image digests and agent scaffold. Apply the generated patch to that snapshot and run official fail-to-pass and pass-to-pass checks. Report the official resolved outcome without replacing the evaluator with Foundation's own tests.

SWE-bench Verified measures issue resolution in Python repositories. SWE-bench Multilingual includes Rust tasks. The Rust slice is a practical first integration target; it still contains library/features outside the initial verified scalar fragment.

## Comparison routes

| Route | Task identity | Formal claim |
|---|---|---|
| Baseline agent | Original repository task | Official tests only |
| Agent + FV tools | Same repository task | Tests plus named proved/checked components |
| Verified kernel repair | Same task, supported function/component | Scoped formal and translation claim plus original tests |
| Resilient port | Adapted task with a new ID | Claim about the adaptation, not official SWE-bench resolution |

Do not translate a Python repository into Resilient and report that as solving the original benchmark. Do not claim the whole repository is verified because one helper was checked.

## Formal repair track

For a supported Rust issue, independently prepare the intended contract, input domain, frame/effects and allowed modifications before generation. Keep the contract locked. The agent proposes code/proofs. Evaluate original repository tests and the immutable formal oracle independently.

A model-generated contract may be evaluated in the intent lane, but it cannot become the sole ground truth for its own patch. Contract and test editing require a separate benchmark track.

## Coverage

Publish original task count, language/task selection rule, eligible formal tasks, verified components and unsupported constructs. Keep unmodified official results separate from adapted/eligible-subset results. Every exclusion has a reason fixed before observing success.

## Extra checks

Independent adversarial cases and regression/effect checks can reject patches that pass the official tests. Preserve both results: "officially resolved; rejected by additional contract" is useful evidence and must not be collapsed into a fabricated official score.

## Execution integrity

Candidate patches cannot change hidden harness/tests, gold data, evaluator configuration, tool permissions or expected answers. Approved source modifications are reviewed in the final diff. External services/network behavior are disabled or explicitly modeled under the benchmark protocol.

## Future repository benchmarks

Vero offers repository-level formal code/proof tasks. SWE-bench Pro/Pro Verified and migration benchmarks can supply harder integration tasks after adapters and task quality are independently audited. Their scores are not directly interchangeable with SWE-bench Verified.
