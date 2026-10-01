# Runtime and agent execution

## "The base for AI to run"

Foundation is a programming/execution substrate for AI-authored agent programs. It supplies typed state, effects, capabilities, verification and evidence-bound execution. It does not assert that every neural network computation or natural-language answer has a formal specification or proof.

Agents may orchestrate models, files, databases, networks and devices through typed component interfaces. The model is an untrusted proposer/oracle unless a narrower property of the component is actually established.

## Execution capsule

An executable capsule binds source/spec/profile/target hashes, accepted evidence, allowed capabilities, input validation, environment assumptions, resource limits and observation hooks. The runtime loads only the artifact covered by the selected policy.

Capabilities are explicit values/contracts. An unverified external component cannot acquire arbitrary effects merely because a verified caller invoked it. Response values are checked at the declared interface; semantic properties of an external service remain assumptions unless supported evidence exists.

## Failure semantics

Distinguish domain error, denied capability, external timeout, resource exhaustion, fault/reset and invariant/monitor violation. Do not disguise them as successful default values. If an assumption is observably violated, stop/degrade according to the accepted policy and invalidate dependent runtime assurance.

## Stateful execution

State transitions and persistent effects are explicit. Checkpoints bind input epoch and artifact identity. A resumed execution under changed source/spec/environment cannot reuse its old acceptance blindly.

## Runtime proof boundary

Runtime source can be modeled/proved for a fragment. That proof does not establish native binary semantics, OS scheduling guarantees or physical hardware behavior without additional obligations/assumptions. The execution record must make the remaining boundary visible.

## Performance

Static proof artifacts should not require an SMT call on every ordinary execution. Runtime validation/monitors are selected for external/precondition assumptions and measured separately. Proof generation, proof checking, compilation and execution each have their own latency and memory figures.

## Interoperability modes

Verified component; contract-assumed component; monitored/tested component; unrestricted experimental component. Execution policy declares which modes are allowed. No wrapper upgrades an unverified library or model into a fully verified component.
