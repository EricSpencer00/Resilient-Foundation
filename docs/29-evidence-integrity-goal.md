# Evidence integrity repair goal

Objective: repair false acceptance at the Resilient/Foundation boundary and ship it after independent regression, real cross-repository acceptance and public CI pass.

Frozen baseline: main f12179b. The existing scalar oracle remains unchanged. Before repair, the public adapter regression suite exposed 13 failures and one untyped exception across nine new test methods. Successful `rz verify-all` exit codes could stand in for skipped Z3 replay; only source filenames were compared at initial import; assurance metadata was ignored during record checking; malformed/duplicate/empty inputs were accepted.

The chosen repair separates compiler regeneration, solver query evidence and artifact integrity. It keeps Resilient as an external trusted compiler, reuses the scalar syntax gate to permit only inert function definitions during regeneration, directly invokes the selected solver, and recomputes every record field. Interactive SMT commands are rejected before execution. Non-query clauses and unauthenticated signatures remain explicitly separate.

Acceptance: the independent adapter tests must pass; real rz/Z3 must regenerate and replay the fixture, reject semantic stale reimport, satisfiable queries and forged claims; scalar end-to-end conformance and the frozen five-case oracle must remain green; saved reports must bind current implementation/tests; free public CI must pass on the released commit. Compute uses the NUC through the MacBook-origin route. No model inference or paid resource is required.

Run ownership: this goal uses `/tmp/foundation-integrity-20261001` on the NUC and adopts the prior goal's `/tmp/foundation-resilient-goal-20261001` binary cache. Both are task scratch and will be removed after durable evidence is copied back. Upstream user files and the existing `.codex/` directory are preserved.

Acceptance evidence: the NUC passed 26 cross-repository checks (18 boundary tests and eight named acceptance cases), 55 scalar end-to-end tests with zero failures/skips, all five frozen oracle cases, 14 Rust conformance tests in debug and release, formatting, Clippy, specification validation and 11 report-policy tests. Reports are saved under `validation/`. The NUC run also exposed Cargo ignoring the selected Rust compiler; a public regression failed before `NativeTools.build_core` was repaired to propagate that selection. Transfer metadata and remote PATH setup were corrected before recording the final successful runs.

Release completion requires green public GitHub checks and merge. The goal tool and GitHub checks retain that final release status; the acceptance reports establish the tested implementation identities.
