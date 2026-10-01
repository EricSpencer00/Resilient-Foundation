# Intent, NLP and autoformalization

## Three input modes

| Input mode | Interpretation | Evidence |
|---|---|---|
| Free prose | LLM proposes requirements, assumptions and clauses | Traceability, accepted decisions and independent validation |
| Controlled language | Versioned grammar/templates with formal interpretation | Deterministic parsing plus a parser/template preservation obligation |
| Formal executable spec | Typed semantic artifact | Direct checking of well-formedness and code correspondence |

An input mode is recorded in the bundle. A polished paraphrase is not evidence of equivalence to raw prose.

## Requirement ledger

Each atomic requirement has a stable ID, exact source location, text, input domain, units, proposed formal clauses, examples/counterexamples, decision state and provenance. Traceability is many-to-many: one requirement may need several clauses, and one clause may enforce several requirements.

Each accepted requirement MUST have at least one clause/observation obligation or an explicit out-of-scope decision. Each clause MUST link to a requirement, a semantic-definition dependency or a declared environment assumption. An out-of-scope decision prevents a whole-request exactness claim.

## Ambiguity handling

Examples: integer overflow, sorting tie-breaks, duplicate requests, failure after an external action, time units, partial network failures and what "fast" means. The system records alternatives with distinguishing examples. It may resolve them from an already accepted domain policy or exact template. Otherwise it returns NeedsDecision.

Normal generation continues automatically within an accepted interpretation and capability budget. Human decisions are required at actual meaning changes, not every proof-search or compiler step.

## Spec validation

Use positive input/output examples, invalid-input examples, wrong-output examples, independent domain oracles, mutation tests, consistency and satisfiability checks. These can reveal misinterpretation. Passing a finite validation suite does not prove complete free-prose faithfulness.

A generated implementation cannot be the sole oracle for the specification it generated. LLM judges may help search and repair; their votes are never kernel evidence.

## Controlled-language first profile

The initial template library covers total scalar functions, bounded collection transforms and explicit transactional state updates. Template parameters are typed. A pretty-printer can provide an exact controlled-language rendering of the canonical AST, but a round trip through that rendering proves only parser/renderer consistency unless template semantics is also justified.

Example accepted sentence: "For an integer x, return x if x is nonnegative, and return zero otherwise." Its formal domain includes all i64 values; its result equation is an if-expression. There is no implicit exclusion of boundary values.

## Search discipline

Lock the accepted spec. The model may edit candidate code and proof hints. Spec repair is a separate action producing a new decision/version; the search engine cannot silently remove a difficult requirement, strengthen a precondition, insert assume(false) or alter the oracle.

Closest prior art includes FRET, VeriSpecGen, Verus-SpecGym and AlphaVerus. See research/references.md. Their existence rules out calling NLP-to-verified-code itself a new area.

## Implemented scalar boundary

The current [intent adapter](../foundation/intent.py) implements one exact controlled sentence under `nonnegative-i64-v1`. It records an accepted typed ledger and locks the generated spec IR. Other prose returns `NeedsDecision`; the interactive Codex candidate does not set its own requirement or acceptance state.
