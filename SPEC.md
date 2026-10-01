# Normative specification index

Specification version: **0.1.0-draft**. Working project name: **Resilient Foundation**. Repository visibility: **private**. Remote repository: https://github.com/EricSpencer00/Resilient-Foundation. Owner: **Eric Spencer**.

## Authority

The prose documents define semantics and obligations. JSON Schema files define wire shapes, not the truth of the values placed in them. The requirement registry links mandatory commitments to documents and work packages. Examples are illustrative and carry that label. Any conflict between normative documents is a specification defect and blocks release; an implementation must not choose the most convenient interpretation.

MUST, MUST NOT, SHOULD and MAY have their ordinary standards meanings. A MUST is a release obligation for the milestone that claims the corresponding capability, not an assertion that draft code already implements it.

## Specification map

| Document | Purpose |
|---|---|
| [00 Requirements](docs/00-requirements.md) | Product requirements and mandatory boundaries |
| [01 Architecture](docs/01-system-architecture.md) | Components, data flow and ownership |
| [02 Correctness](docs/02-correctness-contract.md) | Exact equivalence, refinement and trust composition |
| [03 Intent](docs/03-intent-and-autoformalization.md) | NLP, controlled language, ambiguity and accepted intent |
| [04 Language](docs/04-language.md) | Rust-familiar Resilient profile and supported fragments |
| [05 Semantic core](docs/05-semantic-core.md) | Types, arithmetic, transitions and canonical artifacts |
| [06 Translation](docs/06-translation-and-codegen.md) | Compiler obligations, validation and native trust |
| [07 Verification](docs/07-verification-and-properties.md) | Safety, temporal, graph, relational and quantitative tasks |
| [08 Proof graph](docs/08-proof-graph.md) | Dependency evidence, search and invalidation |
| [09 Certificates](docs/09-certificates-and-trust.md) | Assurance classes, checking and manifest binding |
| [10 Recovery](docs/10-fault-recovery-effects.md) | Reset/retry, persistence and observable effects |
| [11 Resources](docs/11-time-energy-probability.md) | Joint time/energy/reliability analysis |
| [12 Runtime](docs/12-runtime-agent-execution.md) | Agent execution and capability interfaces |
| [13 Rust interoperability](docs/13-rust-ecosystem-and-interoperability.md) | Libraries, proofs and performance routes |
| [14 Resilient integration](docs/14-resilient-integration.md) | Existing mechanisms and concrete gaps |
| [15 Evaluation](docs/15-evaluation-matrix.md) | Independent model, package and runtime lanes |
| [16 Models](docs/16-model-evaluation.md) | New-model protocol and paired comparisons |
| [17 SWE-bench](docs/17-swebench.md) | Real-repository adapters and score separation |
| [18 Performance](docs/18-package-performance.md) | Fixed workloads, resource measurements and gates |
| [19 Adversarial suite](docs/19-soundness-and-mutation-suite.md) | False acceptance, vacuity, mutants and independent oracles |
| [20 CI/release](docs/20-ci-release-gates.md) | Capability-specific release requirements |
| [21 Roadmap](docs/21-roadmap.md) | Milestones, dependencies and exit conditions |
| [22 Research](docs/22-research-positioning.md) | Inspiration, baselines and provisional contributions |
| [23 API](docs/23-api-cli.md) | Rust interfaces, tool protocol and CLI behavior |
| [24 Example](docs/24-reference-example.md) | One exact scalar task through the pipeline |
| [25 Extensions](docs/25-concurrency-and-extension-horizon.md) | Concurrency, floats, distributions and other languages |

## Machine-readable artifacts

- [requirements/registry.json](requirements/registry.json): commitments and their acceptance work.
- [schemas](schemas/README.md): versioned shapes and cross-file checks.
- [profiles/scalar-wrapping-v1.json](profiles/scalar-wrapping-v1.json): first semantic profile.
- [profiles/backend-capabilities.json](profiles/backend-capabilities.json): proposed routes, all initially planned.
- [eval/profiles.json](eval/profiles.json): suggested budgets and measurement protocols.
- [eval/metrics.json](eval/metrics.json): formulas and denominators.
- [benchmarks/adversarial-catalog.json](benchmarks/adversarial-catalog.json): independently specified case families.
- [examples](examples/README.md): illustrative artifacts with no fabricated proof results.

A JSON Schema validator is not an SMT solver, proof kernel, intent oracle or compiler validator. These roles remain separate throughout the design.
