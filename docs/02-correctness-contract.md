# The correctness contract

## Define "1:1"

Let S be the accepted specification, P the implementation, E a declared environment and O an observation projection. Let Beh(X,E) include successful, erroneous and nonterminating executions under the selected semantics.

For a complete deterministic executable specification, the required statement is:

~~~text
for every admissible input x and environment E:
  O(Beh(P,x,E)) = O(Beh(S,x,E))
~~~

Internal compiler steps and proof-search events are hidden only if O declares them unobservable. Errors, externally visible actions, secret-dependent timing and termination cannot be hidden when the property depends on them.

This is observable equivalence. It does not require a bijection of source lines, states or machine steps.

## General contracts and nondeterminism

A predicate contract usually permits many behaviors. Ordinary implementation correctness establishes:

~~~text
O(Beh(P,E)) is a subset of Allowed(S,E)
~~~

This is refinement. It is not automatically equality. Exact-mode requests with an underdetermined spec must return NeedsDecision or Unsupported until an executable interpretation or explicit choice policy is supplied.

For nondeterministic exact equivalence, prove both trace-set inclusions, including matching input/environment choices. Probability-sensitive claims additionally require equality or the declared bound on measures, not just equality of possible traces.

## Termination and bounds

A postcondition about returned results is partial correctness unless termination is separately established. Exact-mode comparison must include termination/error outcomes or explicitly state a bounded horizon. Bounded equivalence is never advertised as unbounded equivalence.

A finite loop bound is semantic only if the specification itself limits behavior that way. An analysis cutoff is evidence scope. These two kinds of bounds must have different fields.

## Composing translations

For representations A -> B -> C, an equivalence chain requires compatible observation maps and checked preservation at every edge. Refinement composes with compatible simulations. An arbitrary mix of evidence does not upgrade refinement into equivalence.

The intended chain is:

~~~text
accepted executable spec
  <-> source semantic IR
  <-> candidate semantic IR, under the required relation
  <-> bytecode/Rust representation
  <-> modeled target execution
~~~

The original prose is linked by interpretation/provenance/validation, not by an unrestricted logical equivalence theorem.

## Trust statement

Every accepted result states its checker/kernel, encoding soundness, source/target semantic model, assumptions and unresolved deployment boundary. A theorem about VM source remains conditional on compilation and actual platform execution unless those boundaries have their own evidence.

"Fully accurate" is allowed only for the specific accepted formal relation and declared artifact/profile scope. It is not a claim that unstated user intent or unmodeled hardware behavior has been proved.
