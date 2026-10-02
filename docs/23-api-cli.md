# Rust API, CLI and AI tool protocol

The scalar CLI below is implemented. The general Rust analysis traits, model tools and expanded commands remain planned. [Implementation status](26-implementation-status.md) records the current supported fragment.

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

## Implemented scalar CLI

Run from the checkout root with the development requirements installed:

~~~text
python -m foundation intent request.txt
python -m foundation source candidate.rz
python -m foundation build --request request.txt --candidate candidate.rz --out artifacts/fresh
python -m foundation check artifacts/fresh
python -m foundation run artifacts/fresh --input '{"x":"-7"}'
~~~

Activate `.venv` for the `bin/foundation` launcher, or use `.venv/bin/python -m foundation`. Global `--solver`, `--cargo` and `--rustc` select executable paths before the subcommand. `build` accepts `--timeout-ms` in 1..60000; build/check/run accept the supported `--policy scalar_source_exact_trusted_rust_v1`. Output directories must be fresh. Rejected builds preserve inspectable intermediate evidence and never create an accepted capsule.

The controlled requirement is the exact shipped nonnegative template. Other prose is `NeedsDecision`. Source supports one `fn name(int x, bool flag) -> int|bool` with total return/if blocks and pure scalar expressions; loops, helpers, contracts, effects and extra declarations are `Unsupported`. i64 JSON inputs are canonical decimal strings; JSON integer inputs are rejected to avoid precision loss.

`check` reconstructs source/target obligations and runs the actual solver; it does not accept the producer's result merely because hashes match. `run` repeats checking and executes only the exact validated binary, comparing the observation with reference evaluation. The prototype trusts Z3, the restricted encodings/reference runtime, Rust compilation, OS and hardware. It does not satisfy `strict_native_exact`.

## Implemented Resilient evidence CLI

The repository-boundary route inventories an existing Resilient checkout and imports its versioned contract certificates:

~~~text
python -m foundation resilient inspect --root /path/to/Resilient
python -m foundation resilient import-cert --root /path/to/Resilient \
  --source /path/to/cert_demo_pass.rz \
  --certificate /tmp/contract-certificate.json \
  --certificate-dir /tmp/proofs --rz /path/to/rz --z3 /usr/bin/z3 \
  --out /tmp/resilient-evidence.json
python -m foundation resilient verify-evidence --evidence /tmp/resilient-evidence.json \
  --root /path/to/Resilient --source /path/to/source.rz \
  --certificate /tmp/contract-certificate.json --certificate-dir /tmp/proofs \
  --rz /path/to/rz --z3 /usr/bin/z3
~~~

The import remains `artifact_checked` without direct solver replay. `--rz` regenerates certificates from current pure function definitions and requires matching artifacts. `--z3` replays every embedded and manifest query directly; only those queries gain `solver_checked` evidence. Clauses without queries remain compiler-reported. Without `--rz`, the source binding is explicitly `associated_only`. `verify-evidence` recomputes every field and required tool identity, rejecting stale records, forged assurance and omitted replay. Old v1 records require regeneration. See [the full integration boundary](28-resilient-evidence-package.md) for capability limits.

## Planned expanded CLI

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

These expanded commands are design vocabulary. They are not aliases for the implemented scalar CLI; unsupported command names fail visibly.

## Agent tool actions

propose_requirements, inspect_requirement, propose_candidate, request_analysis, inspect_counterexample, propose_proof_hint, check_translation, inspect_evidence and request_execution. Each action has typed input, artifact IDs, budget and policy context. Spec changes create a separate version/decision.

A model cannot request Proved as an action or set its own acceptance state. Tool output includes source diagnostics and current result axes. Unknown cannot be handled by replacing a missing tool with an LLM judge.

## Exit behavior

Implemented scalar process exit codes: 0 required policy satisfied; 2 refuted; 3 Unknown/Timeout/ResourceLimit; 4 Unsupported; 5 InvalidEvidence; 6 NeedsDecision; 1 operational error. JSON output remains authoritative, and multiple obligations are aggregated without hiding required failures.

## Error diagnostics

Include stage, outcome, artifact/obligation ID, source span when available, expected/actual semantic profile, supported fragment and reproduction input. Avoid dumping credentials or private model reasoning; user-visible proof artifacts and necessary provenance suffice.

## API stability

Wire schemas and semantic profiles are versioned separately from Rust crate APIs. Breaking semantic changes create new identities; a parser that can read an old shape does not necessarily support its old semantics.
