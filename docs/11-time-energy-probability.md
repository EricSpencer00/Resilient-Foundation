# Time, energy and probabilistic contracts

## Joint event

Let J mean successful completion by D, cumulative energy <= B, and no unsafe observable action. For a finite MDP, one possible robust query is:

~~~text
inf over schedulers sigma in declared class:
  Pr_sigma[J] >= p
~~~

State records elapsed time, total energy, retries, snapshots/restores, commit/error status and relevant device/fault state. A policy comparison fixes the same input, fault, power and cost assumptions.

## Correlations

Do not multiply marginal success, deadline and energy probabilities without a justified independence relation. Faults, energy availability, input paths and retries may correlate. The model must preserve the correlations needed for the query.

## Target profiles

Separate measured point estimates, assumed random distributions, conservative worst-case bounds and model-derived results. Every profile has target/device/compiler identity, calibration method, units, uncertainty and version. A fixed AST loop multiplier is not a verified WCET bound.

Loop bounds, call costs, retry/checkpoint/restore costs and runtime monitors enter the total budget. GPU/CPU/local/cloud hardware comparisons must use the same workload and report concurrency and power-measurement limitations.

## Numerical evidence

Exact rational finite-model checking is preferred where feasible. Otherwise use rigorous intervals/residual bounds and state the numerical tolerance/rounding method. If a threshold lies inside the unresolved interval, return Unknown, not a favorable point estimate.

Statistical model checking reports sampling procedure, seeds, stopping rule, confidence/error level and model assumptions. An empirical success rate alone is not a lower-probability guarantee. Adaptive/repeated testing requires a valid sequential/multiple-testing procedure.

## Evidence connection

A quantitative result is about its finite model until extraction/preservation is established. Profile assumptions and distributions remain conditional even after encoding correctness is proved. A runtime monitor may enforce a budget, but that does not prove the budget can always be met while preserving progress.

ETAP, Rely and Caesar/HeyVL already cover adjacent quantitative work. Foundation's prospective contribution is the specific combination with source-faithful reset/effect semantics and checked translation evidence.
