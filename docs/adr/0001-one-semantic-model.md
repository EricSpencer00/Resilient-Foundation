# One semantic model, many analysis routes

Status: accepted design decision, 0.1.0-draft.

## Decision

Use a versioned typed execution model with explicit observations, faults, errors and costs. Property languages/routes consume supported views with preservation obligations. Do not maintain unrelated backend translations and claim their conjunction automatically means source correctness.

## Consequences

This limits initial feature coverage and demands semantic engineering. It makes source-to-model evidence and cross-route comparisons reviewable.

## Validation

The corresponding normative documents, requirement registry and milestone acceptance evidence must agree. This decision does not claim its implementation exists.
