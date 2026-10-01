# Package and executable performance

## Fixed-artifact rule

Package performance uses checked-in code/spec/IR/certificate fixtures and scaling generators with independent expected results. No LLM is needed. New models cannot inflate package speed by producing easier programs.

## Measurements

| Stage | Required measurements |
|---|---|
| Parse/type/canonicalize | Wall/CPU, peak RSS, input bytes/nodes, rejected malformed input |
| Obligation/model construction | Wall/CPU/RSS, formula/model size and source-map size |
| Solver/search | Correct result count, Unknown/Timeout/Memout, wall and aggregate CPU, explored states |
| Proof/witness checking | Independent checking time, RSS, certificate bytes, replay failures |
| Translation validation | Source/target size, relation, time/RSS, accepted/rejected/unsupported |
| Incremental edit | Changed requirement/code/assumption, invalidated/reused nodes, total recheck latency |
| Build | Codegen/compiler time, artifact size and toolchain |
| Runtime | Throughput/latency, allocations/RSS, errors/effects, code size and optional measured energy |

Cold process/cache, warm checker and incremental runs are separate. End-to-end totals include startup/encoding/decoding/checking. Portfolio runs report both elapsed time and summed worker CPU.

## Workload grid

Expression size, bit width, branch count, loop bound, state count, trace count, retry budget and model sparsity vary independently where possible. Arithmetic/profile semantics stay the same within a comparison. A solver timeout is an outcome, not a discarded slow sample.

Finite models scale through predeclared sizes such as 10^3, 10^4 and 10^5 reachable states when the generated model actually reaches those sizes. Record measured reachable states, not just a requested cap.

## Baselines

Direct backend with the same emitted problem measures integration overhead. Hand-written safe Rust with equivalent observable semantics measures executable overhead. Reference interpreter/bytecode/native routes are separate runtime categories. Verus/Creusot/Aeneas comparisons match supported semantics and required assurance, not merely similar source text.

## Repetition and statistics

Pin machine/OS/toolchain, CPU governor/affinity policy, concurrency, compiler flags, warmup and cache policy. Interleave paired candidates/baselines to reduce drift. At least 30 paired samples support exploratory medians; require 200 observations for a p95 gate and 1000 for p99 reporting, or label the tail estimate exploratory.

Use paired bootstrap intervals over latency ratios and show per-case results. Aggregate geometric means only across predeclared comparable workloads; also publish the worst regressions and unsolved outcome counts.

## Proposed engineering targets

These are provisional targets to calibrate at M1, not measured facts:

- Small source/spec edit: interactive diagnostic goal <= 1 second excluding a remote model call, for a declared small profile.
- Checked-evidence cache hit: avoid solver rerun and validate identity/dependencies.
- Native pure scalar output: target median runtime <= 1.15x matched safe Rust; monitors/effect-heavy workloads get separate budgets.
- Proof checking should usually cost less than proof search; publish counterexamples to that expectation.
- Default package: no heavyweight optional solver downloads for a user who does not request the route.

## Regression gates after a baseline exists

Correctness and evidence gates take precedence. Candidate regression thresholds start at +10% median, +20% p95 or +10% peak RSS on a stable matched suite, confirmed by a second clean paired run with uncertainty reported. These are policy defaults, not universal performance guarantees; noisy/insufficient results return Inconclusive.

Publish budget-success curves/ECDF and outcome histograms for verification. Report timeouts with their caps; avoid a solved-only speed chart that rewards skipping hard cases.
