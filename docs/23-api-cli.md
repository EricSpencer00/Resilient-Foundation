# Rust API, CLI and AI tool protocol

The analysis, evidence and CLI interfaces below are planned. The implemented scalar reference API is documented separately in [implementation status](26-implementation-status.md).

## Rust API shape

~~~rust
pub enum CheckOutcome {
    Proved(CheckedEvidence),
    Refuted(ValidatedWitness),
    Unknown(Reason),
    Unsupported(CapabilityMismatch),
    Timeout(BudgetRecord),
    ResourceLimit(BudgetRecord),
    InvalidEvidence(Diagnostic),
    NeedsDecision(Ambiguity),
    Error(Diagnostic),
}

pub trait AnalysisRoute {
    fn capabilities(&self) -> CapabilityManifest;
    fn analyze(&self, task: &TypedTask, budget: &Budget) -> CandidateResult;
}

pub trait EvidenceChecker {
    fn check(&self, obligation: &Obligation, bytes: &[u8])
        -> CheckOutcome;
}
~~~

These types are conceptual; CheckedEvidence is constructible only through the relevant actual checker, not by deserializing a producer's assertion.

## Planned CLI

~~~text
foundation intent propose request.txt
foundation spec validate task.bundle/
foundation generate task.bundle/ --model <snapshot> --budget <profile>
foundation verify task.bundle/ --required-policy <policy>
foundation translate-check task.bundle/
foundation explain task.bundle/ --requirement <id>
foundation run task.bundle/ --capsule <accepted-capsule>
foundation eval model --manifest <pinned-manifest>
foundation eval package --profile <fixed-artifact-profile>
foundation eval runtime --profile <matched-native-profile>
~~~

The Python specification checker and the `foundation-core` Rust reference API/example are implemented. No `foundation` CLI, JSON execution adapter or proof checker is shipped yet.

## Agent tool actions

propose_requirements, inspect_requirement, propose_candidate, request_analysis, inspect_counterexample, propose_proof_hint, check_translation, inspect_evidence and request_execution. Each action has typed input, artifact IDs, budget and policy context. Spec changes create a separate version/decision.

A model cannot request Proved as an action or set its own acceptance state. Tool output includes source diagnostics and current result axes. Unknown cannot be handled by replacing a missing tool with an LLM judge.

## Exit behavior

Proposed process exit codes: 0 required policy satisfied; 2 refuted; 3 Unknown/Timeout/ResourceLimit; 4 Unsupported; 5 InvalidEvidence; 6 NeedsDecision; 1 operational error. JSON output remains authoritative, and multiple obligations are aggregated without hiding required failures.

## Error diagnostics

Include stage, outcome, artifact/obligation ID, source span when available, expected/actual semantic profile, supported fragment and reproduction input. Avoid dumping credentials or private model reasoning; user-visible proof artifacts and necessary provenance suffice.

## API stability

Wire schemas and semantic profiles are versioned separately from Rust crate APIs. Breaking semantic changes create new identities; a parser that can read an old shape does not necessarily support its old semantics.
