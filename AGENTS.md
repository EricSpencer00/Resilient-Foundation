# Agent instructions for Resilient Foundation

This is a private specification repository. Documentation, schemas, examples and evaluation plans are intended repository artifacts.

1. Read SPEC.md and the affected normative document before changing behavior.
2. Preserve the distinction between planned, experimentally validated, solver-checked, kernel-checked and translation-checked capabilities.
3. Never weaken an accepted requirement, edit an evaluator's oracle or relabel Unknown/Unsupported as success to make a task pass.
4. Tie every new assurance claim to its semantic profile, observation model, assumptions, artifact identity and acceptance evidence.
5. Keep changes to EricSpencer00/Resilient separate; its own AGENTS.md applies in that repository.
6. For implementation work, add a public-interface counterexample or conformance case before repairing a substantive semantic defect. Avoid tests that only duplicate an encoder's own logic.
7. Run scripts/validate_spec.py after changing this specification. Once compiler/backend code exists, run the affected conformance and proof checks as well.
8. Do not publish the repository, change visibility, grant access, or distribute private holdout data without an explicit user instruction.
9. Record limitations and actual commands. Do not claim benchmarks or proofs ran when only files or schemas were checked.
10. Do not install a universal set of solvers by default. Implement and evaluate one supported route first.
