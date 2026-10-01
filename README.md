# Resilient Foundation

A Rust-based foundation for AI-generated software whose requirements, executable specifications, implementation, translation evidence and runtime behavior remain connected.

**Status: private design/specification repository, version 0.1.0-draft, 30 September 2026.** The language compiler, proof checker, backend integrations and benchmark runner described here are planned. The specification validator is implemented. A passing specification check is not a program-correctness proof.

The first frontend is [Resilient](https://github.com/EricSpencer00/Resilient), owned by Eric Spencer. Resilient keeps its language/compiler/runtime identity; Foundation supplies shared semantic profiles, obligations, evidence and evaluation protocols.

## The central contract

For a complete deterministic executable specification, accepted implementation and declared environment, the target is equality of **observable behaviors**. The correspondence includes values, errors, effect ordering and termination under the declared bounds. It is not a correspondence between source lines or every internal instruction.

Free-form language becomes an explicit requirement ledger. Controlled language and versioned templates can have exact formal interpretations. An LLM's interpretation of unrestricted prose remains a candidate requiring validation or an accepted decision. That boundary is recorded, never silently converted into a theorem.

## Read this first

1. [Normative specification index](SPEC.md).
2. [Correctness contract](docs/02-correctness-contract.md).
3. [Intent and autoformalization](docs/03-intent-and-autoformalization.md).
4. [Translation and native execution](docs/06-translation-and-codegen.md).
5. [Evaluation matrix](docs/15-evaluation-matrix.md), [model protocol](docs/16-model-evaluation.md), [SWE-bench route](docs/17-swebench.md), and [package performance](docs/18-package-performance.md).
6. [Roadmap and acceptance gates](docs/21-roadmap.md).
7. [Machine-readable work packages](roadmap/work-packages.json).

## Validate the specification

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_spec.py
~~~

This checks schema validity, artifact bindings, traceability, backlog dependencies, examples and deliberately invalid evidence manifests. It makes no calls to an LLM, solver or external service.

## First implementation slice

A scalar Resilient fragment with exact wrapping-i64 semantics, explicit errors, bounded control flow, a reference semantics, source-linked obligations and independent translation checks. Recovery adds defined reset/snapshot boundaries and retry-safe effects. Quantitative and relational analyses extend the same model.

The eventual platform supports general agent programs through typed capabilities and modular verified components. Existing unverified libraries, neural models and external systems remain explicit interfaces with declared assumptions. They do not inherit a whole-system proof from a verified wrapper.

## Evaluation philosophy

Keep separate: **repository tests passed**, **formal contracts proved**, **translation evidence checked**, **intent validated**, **coverage achieved**, and **cost/performance**. New models are evaluated against pinned suites and budgets; package changes are evaluated on fixed artifacts independent of the model.

No current model score, speedup, novelty result or completed end-to-end implementation is claimed in this repository.
