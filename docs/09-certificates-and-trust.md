# Certificates, assurance and trust

## Independent axes

A result has an intent status, formal-verification status, translation status, runtime/deployment status and empirical-validation status. One green check must not hide failures on another axis.

| Evidence class | What it establishes |
|---|---|
| illustrative | An example shape, with no observed proof result |
| empirical | A recorded test/sample result under stated conditions |
| solver_checked | A supported solver reported the claim under its trusted encoding/solver |
| kernel_checked | An accepted kernel/checker validated evidence of the stated formal proposition |
| translation_checked | A supported checker validated the specified source/target relation |
| deployed_bound | The executed artifact matches the accepted build identity; environment assumptions remain |

The last two classes are distinct claim kinds rather than a scalar universal confidence ladder. The result vector and required policy determine execution eligibility.

## Trusted computing base

List parser/type/model extraction assumptions, encoding rules, checker/kernel, external theorem libraries, target/VM semantics, compiler/runtime/OS/hardware assumptions and environment contracts. A narrow checker is a design goal; supporting every solver theory in a new homemade kernel is not the first milestone.

Lean/Rocq or a supported proof-witness checker can anchor initial kernel evidence. Their executable checker and platform remain part of the real-world trust boundary.

## Certificate contents

Artifact identities, exact obligation, theorem/query/proof/model digest, backend/tool/checker versions, evidence class, scope/bounds, assumptions, validation outcome and source map. A replay bundle includes required bytes rather than depending on a mutable external URL.

A signature authenticates bytes and the signer, not theorem soundness or source-to-query correctness. Rerunning an SMT query validates that query subject to solver trust, not its meaning relative to the program.

## Result states

Proved, Refuted, Unknown, Unsupported, Timeout, ResourceLimit, InvalidEvidence, NeedsDecision and Error are distinct. A missing backend returns Unsupported. A timeout is not a refutation. Proved is permitted only for an actually discharged formal obligation; illustrative manifests cannot claim it.

## Acceptance policy

The selected policy declares required axes/classes and capability assumptions. Weak evidence cannot satisfy a stronger gate. Optional diagnostics may fail without changing an unrelated proved claim, but failure of any required obligation prevents whole-artifact acceptance.

The specification validator checks shapes, dependency policy and the integrity of saved experimental reports; it does not discharge program obligations. The scalar `foundation check` command reconstructs the request/source/target relation and reruns actual SMT obligations before acceptance. Its `solver_checked` and `translation_checked` declarations remain conditional on the encoding, Z3, restricted target reader and runtime. Exact native rebuilds bind bytes under compiler trust; they do not establish machine-code equivalence. See [the implemented policy](23-api-cli.md).
