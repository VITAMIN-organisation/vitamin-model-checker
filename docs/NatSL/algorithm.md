# NatSL algorithm reference

This page explains how NatSL is checked, for developers reading or changing the
checker in `model_checker/algorithms/explicit/NatSL/`; the syntax is in the
[knowledge base](../logic_knowledge_base.md#natsl---natural-strategy-logic) and the
model format in [CGS sections](../file_formats.md#cgs-sections).

## Supported fragment

The checker implements a restricted one-goal fragment with bounded natural strategies.

The executable quantifier prefix has the form:

```text
E* A*
```

including purely existential prefixes. The parser also accepts other orders such as
`A{1}x E{1}y:`; `model_checking` then returns a validation error, "This restricted
NatSL[1G] prototype accepts only a two-block E* A* prefix; universal-then-existential
or repeated alternation is unsupported" (`NatSL/core.py`).

The bindings must cover every agent of the model exactly once. On a 2-agent model,
`E{1}x: (x, 1) F goal` fails with "The executable fragment requires a closed binding
prefix covering every model agent exactly once; expected [1, 2], got [1]".

Example:

```text
E{2}controller A{1}opponent: (controller, 1)(opponent, 2) F goal
```

Strategy variables may use multi-character identifiers such as `controller`, `opponent`, and `strategy1`.

Supported temporal goals are `F`, `G`, and `X`, including their negated forms. The operator is uppercase and followed by a space; `not` is lowercase.

The full logic is larger. The NatSL paper, AAMAS 2022 (local copy
`docs/papers/AAMAS22.pdf`, section 3.1, Definition 2), defines

```text
phi ::= p | Es_a^{<=k}. phi | (a, s_a) phi | f(phi, ..., phi) | X phi | phi U phi
```

Here `p` is a proposition, `a` an agent, `s_a` a strategy variable and `k` the
complexity bound: the checker writes `Es_a^{<=k}.` as `E{k}s:` and `(a, s_a)` as
`(s, a)`. Each `f` is a function on truth values; the paper uses them for true,
disjunction and negation ("function 1, function x, y -> max(x, y) and function
x -> -x"). Definition 2 gives no precedence and does not say how far a quantifier
reaches in a formula such as `Es. phi U psi`.

The fragment needs no such rule, because a goal is one operator over one
proposition. Any connective in a goal, as in `E{1}x: (x, 1) F p && q` or
`E{1}x: (x, 1) F (p && q)`, is rejected with the message for every malformed goal:
"Unsupported goal; this prototype accepts F p, G p, X p and their negations, with
an uppercase operator and a space after it". The other logics with a prefix report
`F p && q` as ambiguous and give both readings
([knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)); NatSL
supports neither reading, so it does not offer them.

## Semantics

Quantifier order is preserved by the NatSL parser.

For example,

```text
E{2}x A{1}y: (x, 1)(y, 2) F goal
```

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

The public entry point is `NatSL/core.py` `model_checking(..., mode=)`:

- `mode="space"` (the default): space-oriented lazy search.
- `mode="time"`: time-oriented materialized search.

Both modes are required to agree on satisfiability.

## Implementation map

- `NatSL/core.py`: shared bounded-strategy model-checking core.
- `parsers/formulas/NatSL/parser.py`: NatSL parser.
- `tests/integration/algorithms/natsl/`: semantic regression tests.
- `tests/unit/parsers/formulas/test_natsl_parser.py`: parser tests.
- `tests/fixtures/CGS/NatSL/`: NatSL CGS fixtures.
- `experiments/natsl/`: reproducible scalability experiments.

## Current boundaries

The checker does not claim support for arbitrary Strategy Logic, repeated quantifier alternation, arbitrary LTL objectives, recall strategies, or epistemic guards.

Unsupported fragments are rejected explicitly.
