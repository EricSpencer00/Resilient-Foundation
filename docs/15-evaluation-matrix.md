# Evaluation matrix

The package and the model are different experimental subjects. A new model must not change the fixed artifact corpus used to measure package correctness or speed.

## Five lanes

| Lane | Question | Inputs held fixed | Main results |
|---|---|---|---|
| A: Intent/specification | Does the model formalize the intended task? | Requirement oracle, task/domain, budget and accepted templates | Spec alignment, omissions, wrong inputs/outputs, ambiguity handling |
| B: Code/proof generation | Can it implement a locked spec and discharge required obligations? | Formal spec, profile, harness, checker, tool budgets | Checked solution rate, proof rate, time/cost per accepted result |
| C: Repository engineering | Does verification help fix real issues? | Repo/task/evaluator snapshot and agent scaffold | Official tests resolved, independent regressions, formal coverage separately |
| D: Package soundness/performance | Does the deterministic package check claims correctly and efficiently? | Code/spec/IR/proof fixtures; no LLM | False acceptance, supported coverage, latency, RSS, proof size |
| E: Executable/runtime | Does produced code preserve behavior and run efficiently? | Inputs, semantics, target/toolchain and baseline | Translation evidence, differential failures, runtime ratio, code size |

The scoreboard is a vector. No composite score may hide false acceptance behind speed or average the five lanes into a universal "correctness percentage."

## Existing benchmark roles

- SWE-bench Verified: broad repository-test outcome; its core tasks are Python projects.
- SWE-bench Multilingual: native Rust repository tasks are especially relevant.
- Verina: modular specification/code/proof tasks.
- Verus-SpecGym: Rust-specification alignment against independent tests/adversarial cases.
- Vericoding benchmark: fixed formal-spec-to-code/proof tasks in several languages.
- AlgoVeri: aligned algorithm tasks for cross-language comparison.
- Vero: repository-level verified code generation.
- SMT-COMP/SV-COMP-style fixed problems: backend correctness/performance protocols, using matching categories only.
- Foundation adversarial and translation cases: arithmetic, fault/effects, evidence binding, unsupported states and target mismatch.

These are candidate adapters and references, not downloaded suites or executed results. Official and adapted tasks have separate identifiers and denominators.

## Headline model metric

CheckedSolutionRate(policy) = count of task attempts satisfying independent requirement validation, task oracle, required formal obligations, required translation evidence and no forbidden edits / all launched task attempts.

The policy and achieved assurance axes are displayed alongside the rate. This is success under a declared formal/validation policy, not proof of arbitrary-prose intent. Timeouts, Unsupported, invalid evidence, budget exhaustion and missing proofs count as not solved. Environment-invalid tasks are separately disclosed with the predeclared exclusion rule.

## Funnel

Publish raw counts at each stage: launched -> parsed -> supported -> independent spec validation passed -> functional oracle passed -> formal obligations discharged -> translation checked -> accepted. Also report supported/all and accepted/supported. A tiny accepted subset cannot be advertised as broad coverage.

## Refresh policy

Freeze a versioned public core for comparison across model releases. Add new held-out, independently authored cases in a separately versioned challenge set. Do not silently replace hard tasks or merge new data into old scores. Package releases rerun fixed artifacts; model releases rerun the same end-to-end tasks under the same package.

No paid model evaluation or recurring automation is initiated by this specification.
