# NatSL - Algorithm Reference

NatSL is implemented under `model_checker/algorithms/explicit/NatSL/`.

## Supported fragment

The current checker implements a restricted one-goal fragment with bounded natural strategies.

The executable quantifier prefix has the form:

    E* A*

including purely existential prefixes.

Example:

    E{2}controllerA{1}opponent:
    (controller,1)(opponent,2)Fgoal

Strategy variables may use multi-character identifiers such as `controller`, `opponent`, and `strategy1`.

Supported temporal goals are `F`, `G`, and `X`, including their negated forms.

## Semantics

Quantifier order is preserved by the NatSL parser.

For example,

    E{2}xA{1}y:(x,1)(y,2)Fgoal

asks for an existential bounded strategy for `x` that succeeds against every admissible bounded strategy for `y`.

Mixed prefixes are evaluated directly and are not decomposed into independent NatATL checks.

## Natural strategies

Natural strategies are represented as ordered condition/action decision lists.

The quantifier bound limits their complexity.

## Exact action pruning

NatSL uses exact action pruning.

When a strategy selects an action, joint actions inconsistent with that choice are removed.

If the selected action is unavailable in a covered state, the strategy profile is inadmissible. NatSL does not introduce an implicit idle-action fallback.

## Execution modes

The two public implementations share the same semantic core:

- `Alternated/natSL.py`: space-oriented lazy search.
- `Sequential/natSL.py`: time-oriented search.

Both modes are required to agree on satisfiability.

## Implementation map

- `NatSL/core.py`: shared bounded-strategy model-checking core.
- `parsers/formulas/NatSL/parser.py`: NatSL parser.
- `tests/unit/algorithms/natsl/`: semantic regression tests.
- `tests/fixtures/CGS/NatSL/`: NatSL CGS fixtures.
- `examples/NatSL/`: runnable examples.
- `experiments/natsl/`: reproducible scalability experiments.

## Current boundaries

The checker does not claim support for arbitrary Strategy Logic, repeated quantifier alternation, arbitrary LTL objectives, recall strategies, or epistemic guards.

Unsupported fragments are rejected explicitly.
