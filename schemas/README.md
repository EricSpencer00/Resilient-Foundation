# Wire schemas

Schemas use JSON Schema Draft 2020-12 and prohibit unexpected properties on the primary artifact records. They validate shape, not theorem truth.

Cross-artifact checks in scripts/validate_spec.py validate references, bounds, identities, dependency cycles and status-policy consistency. Actual proof/translation checking is planned and must be performed by the dedicated route.

Integer values that can exceed exact JSON-number precision are decimal strings. Hashes bind exact artifact bytes; a matching hash does not prove source/model correspondence.

Current illustrative instances live in examples/nonnegative/. The checked Resilient integration record lives in validation/resilient/ and binds a real contract certificate plus SMT-LIB2 manifest to the cross-repository replay. Negative evidence manifests are specification-policy cases, not forged real certificates. Schema changes update their version and affected examples.
