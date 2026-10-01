# Proof and evidence graph

## Inspiration

Assuming the user's reference is prooftree.ai, its public material describes a verified human-AI mathematics workspace and persistent reasoning. Foundation adopts the useful idea of inspectable, reusable evidence connected to the original work. Its private implementation and any spec-to-code guarantee were not audited. This is inspiration, not a claim of copying an available proof kernel.

Proof search may use trees; accepted dependencies form a typed DAG. A visual graph is not itself proof evidence.

## Node types

Raw request, requirement, accepted decision, formal clause/spec, semantic profile, source/IR/target artifact, obligation, theorem, proof certificate, checked witness, empirical test, environment assumption, policy decision and limitation.

Edges have semantics: formalizes, implements, generates, proves, validates, assumes, translates, observes, supersedes and depends_on. Proof aggregation traverses only permitted evidence edges; a prose explanation or successful test cannot satisfy a theorem node.

## Obligation identity

Include proposition/relation, source and target IDs, quantifiers, input domain, observation, bounds, environment, theory/profile and dependencies. A proof of a similarly worded but different proposition is not reusable evidence.

## Graph acceptance

Required obligations are closed only by an appropriate checked result. A required unresolved dependency prevents the corresponding capability claim. Cycles in theorem/acceptance dependencies are rejected unless an explicit, sound induction/coinduction rule establishes them.

An independently satisfiable input/environment witness and requirement completeness decision prevent vacuous whole-request claims. These checks do not prove that every raw-prose nuance was captured.

## Search and repair

LLMs propose code, invariants, proof steps and local repairs. Search records budget, candidate ancestry, verifier feedback and rejected changes. Reward is checked progress under a locked spec; editing the spec or evaluation oracle is not progress.

Proof sketches, chain-of-thought and judge consensus may guide search but are not accepted proof objects. The evidence graph stores public proof artifacts and required provenance, not private model reasoning traces.

## Invalidation

A changed spec, profile, code, observation, assumption or tool version invalidates dependent nodes. A checked dependency analysis may retain unrelated nodes. "Same annotation count" and unchanged filenames are insufficient.

## UI contract

Display separate intent, formal proof, translation, runtime and empirical statuses. A user can follow a requirement to the claim and exact artifact. Expand assumptions and unsupported scope without forcing users to learn backend internals for routine tasks.
