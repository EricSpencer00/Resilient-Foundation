# New-model evaluation protocol

## Factorial comparison

For each chosen model snapshot run:

1. A pinned baseline agent with native tools and no Foundation verifier.
2. The same scaffold plus Foundation's verifier/evidence tools.
3. For supported tasks, the locked-spec Resilient pipeline.
4. Ablations removing one component: independent spec validation, translation validation, proof graph/cache, or recovery effect checks.

Keep task, model, scaffold, initial context and total budget comparable. A pipeline that performs extra calls reports their cost; do not present a scaffold comparison as a pure model ranking.

Native repository runs and language-ported algorithm tasks are different tracks. A Rust/Resilient vs Dafny/Lean claim requires aligned requirements and matched domains, not arbitrary leaderboard scores.

## Model manifest

Provider, immutable snapshot where available, model ID, request date, effective serving version, reasoning/temperature settings, context limit, tool format, tokenizer/accounting method, pricing snapshot, retries, region/runtime, adapter/scaffold/package commits and task-split hash.

If a provider silently updates an alias, create a new serving-date cohort. Do not claim exact model reproducibility when the API does not expose a snapshot. Local models record weights/tokenizer/runtime/quantization/hardware hashes.

## Budget profiles

Suggested budgets live in eval/profiles.json. They are design defaults, not authorized spending. Every real run declares wall time, token/tool-call limits and monetary/compute cap. Model time, solver CPU, compiler time and checker time are separate, with total wall/CPU/cost also reported.

Stop on exhausted budget. A repair rollout belongs to the same attempt only within its declared budget. pass@1 is one attempt under that policy; repeated seeds, pass@k and best-of-n are separately labeled.

## Comparison statistics

Use paired tasks and matched seeds where meaningful. Publish all raw outcomes, paired success differences and 95% bootstrap confidence intervals clustered by task/repository as appropriate. Small strata carry uncertainty; do not claim a ranking from one convenient task.

Report total spend / accepted results, including costs of failed attempts. If no task is accepted, cost per accepted result is undefined, with spend and zero successes shown. Tokens/calls/CPU are comparable secondary measurements even when provider pricing differs.

## Leakage control

Freeze specs/oracles/evaluator outside the agent-writable tree. Do not expose gold patches, hidden tests, accepted formal references or private evaluation logs. Audit attempts to alter tests, introduce assumptions, copy expected outputs, narrow inputs or exploit harness behavior.

Public benchmarks may be in model training. Label contamination risk and maintain independently authored/time-separated challenge tasks. A private file is not automatically uncontaminated; provenance and exposure history are recorded.

## Independent intent evaluation

A model can produce code that proves a weak spec. Evaluate the spec against independent intended inputs, wrong outputs, rejected inputs and semantic mutants. If the requirement is incomplete, record NeedsDecision; count that as an appropriate abstention in ambiguity metrics, not as an implemented solution.

## Model admission

A new model does not get a permanent trust exemption for scoring well. Its candidates must satisfy the same deterministic policy. Admission can select a cost/latency/coverage Pareto frontier; correctness gates remain per artifact.

Do not hardcode today's model winner. Re-evaluate on the versioned protocol as new models become available.
