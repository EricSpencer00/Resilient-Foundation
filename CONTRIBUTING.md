# Contributing

Start with one work package in roadmap/work-packages.json whose dependencies are satisfied. A capability remains planned until its acceptance artifacts exist and have been reviewed against the normative specification.

A contribution describes: the triggering problem, changed semantics or behavior, supported fragment, independent expected result, validation performed and remaining assumptions. For a semantic correction, include a case that distinguishes the old and new behavior.

Specification changes update the requirement registry, schema/example where relevant, work-package links and affected evaluation metric. A change to an observation model or arithmetic profile creates a new profile identity; it must not silently reinterpret existing certificates.

Implementation changes expose stable Rust or CLI boundaries and explicit unsupported outcomes. Optimizations preserve the same observations and preconditions. Ported benchmark tasks record the original task, adaptation, retained requirements, excluded requirements and evaluation denominator.

This private repository has no public license grant. Dependency licenses and redistribution requirements must be recorded when third-party code is actually introduced.
