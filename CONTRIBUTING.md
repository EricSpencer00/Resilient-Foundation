# Contributing

Start with one work package in roadmap/work-packages.json whose dependencies are satisfied. A capability remains planned until its acceptance artifacts exist and have been reviewed against the normative specification.

A contribution describes: the triggering problem, changed semantics or behavior, supported fragment, independent expected result, validation performed and remaining assumptions. For a semantic correction, include a case that distinguishes the old and new behavior.

After installing the specification dependencies as described in README.md, run `make check`. The Rust core has no third-party dependencies. Use `in_progress` plus existing `implementation_artifacts` paths when a work package has partial code; the validator rejects completion labels until a separate acceptance check is defined. A passing test does not close a proof milestone.

Specification changes update the requirement registry, schema/example where relevant, work-package links and affected evaluation metric. A change to an observation model or arithmetic profile creates a new profile identity; it must not silently reinterpret existing certificates.

Implementation changes expose stable Rust or CLI boundaries and explicit unsupported outcomes. Optimizations preserve the same observations and preconditions. Ported benchmark tasks record the original task, adaptation, retained requirements, excluded requirements and evaluation denominator.

This repository currently has no explicit public license grant. Dependency licenses and redistribution requirements must be recorded when third-party code is actually introduced. Public visibility does not by itself grant permission to reuse the code; add a project-approved license before making a reuse claim.

## Guarded agent readiness

Commit and push the complete change, then run
`agent-scripts/ready-or-bail.sh --pr N` from this checkout. This is the
agent draft-to-ready route. It requires a clean tree, a pushed PR head
containing current `origin/main`, substantive implementation and new tests,
and no protected test, dependency or workflow edits. It runs `make check`,
a locked build, the full real solver/native gate, saved Resilient query
replay and specification validation. Failed gates leave the PR draft;
success applies `agent-vetted`. Enable squash auto-merge only after this
script succeeds, and verify the final merged state.

The scalar gate's scratch evidence is removed on exit. Its checked-in
acceptance report must already match the committed implementation. When
shared CLI or integration code changes, regenerate the real source-bound
Resilient integration report using `scripts/run_resilient_integration.py`;
do not update recorded hashes without executing that gate.
