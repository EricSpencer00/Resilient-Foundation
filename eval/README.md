# Evaluation specification

Start with docs/15-evaluation-matrix.md. Profiles, formulas and adversarial case families are machine-readable. No model/provider winner is embedded.

The eval runner and external dataset adapters are planned. Current validation checks the consistency of this protocol, not actual SWE-bench scores or package runtime. Files marked illustrative are not collected results.

Every real experiment pins model serving identity, package/scaffold/checker revisions, task split, hardware/toolchains and budgets. Separate official repository results, adapted tasks, fixed-artifact package measurements and runtime ratios.

No private holdout/oracle is included. The development examples in this repository must not later be called hidden evaluation data.
