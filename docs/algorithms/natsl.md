# NatSL algorithm reference

This page explains how NatSL is checked, for developers reading or changing the
checker in `model_checker/algorithms/explicit/NatSL/`; the syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#natsl---natural-strategy-logic) and the
model format in [CGS sections](../reference/file_formats.md#cgs-sections).

## Model

- Type: `CGS`
- A binding `(x, 1)` makes strategy variable `x` play agent 1; the bindings of a
  formula must cover every agent of the model exactly once.

## Formula language

Parser: `parsers/formulas/NatSL/parser.py`

The checker runs a fragment with one temporal goal per formula. A natural
strategy is an ordered list of condition/action rules: an earlier matching
condition wins over a later one, and `T` can be used as a default condition. The
bound `k` of a quantifier `E{k}x` or `A{k}x` limits the strategy's complexity. The quantifier prefix has
the form `E* A*`, purely existential prefixes included, as in:

```text
E{2}controller A{1}opponent: (controller, 1)(opponent, 2) F goal
```

- Prefix order: the parser also accepts other orders such as `A{1}x E{1}y:`;
  `model_checking` then returns a validation error, "This restricted NatSL[1G]
  prototype accepts only a two-block E* A* prefix; universal-then-existential
  or repeated alternation is unsupported" (`NatSL/core.py`).
- Bindings: on a 2-agent model, `E{1}x: (x, 1) F goal` fails with "The
  executable fragment requires a closed binding prefix covering every model
  agent exactly once; expected [1, 2], got [1]".
- Goals: `F`, `G` and `X` over one proposition, and their negations, as in
  `E{1}x:(x,1) not F goal` or `!F goal`. The operator is uppercase and followed
  by a space; `not` is lowercase. Strategy
  variables may be multi-character identifiers such as `controller`.
- Connectives in a goal: `E{1}x: (x, 1) F p && q` and
  `E{1}x: (x, 1) F (p && q)` are both rejected with "Unsupported goal; this
  prototype accepts F p, G p, X p and their negations, with an uppercase
  operator and a space after it". The other logics with a prefix report
  `F p && q` as ambiguous and give both readings
  ([knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective));
  NatSL supports neither reading, so it does not offer them: a goal is one
  operator over one proposition.

## Semantic denotations

The checker searches bounded natural strategies in the order of the prefix: for
`E{2}x A{1}y: (x, 1)(y, 2) F goal` it looks for a strategy of complexity at most
2 for `x` that wins against every admissible strategy of complexity at most 1
for `y`. Each existential profile is first checked against unrestricted
opponents, with [NatATL](natatl.md) pruning and a CTL check of the
goal. A yes there is final; a no is not, so the bounded universal strategies are
then enumerated.

- Exact action pruning: when a strategy selects an action, the model's joint
  actions inconsistent with that choice are removed, and the goal is then
  checked on the pruned CGS by the CTL backend. If the selected action is
  unavailable in a covered state, the strategy profile is inadmissible; there
  is no implicit idle-action fallback.
- Modes: `model_checking(..., mode=)` in `NatSL/core.py` runs a space-oriented
  lazy search (`mode="space"`, the default) or a time-oriented materialized
  search (`mode="time"`). Both must agree on satisfiability.

## Theory vs implementation

Table 1 sets the paper next to the code. In the paper's grammar `p` is a
proposition, `a` an agent, `s_a` a strategy variable, `k` the complexity bound
and `f` a function on truth values:

**Table 1: NatSL theory and implementation.**

| Aspect | Paper (AAMAS 2022, Definition 2) | Code |
| :--- | :--- | :--- |
| Grammar | `phi ::= p \| Es_a^{<=k}. phi \| (a, s_a) phi \| f(phi, ..., phi) \| X phi \| phi U phi` | One goal `F`, `G` or `X` over one proposition, or its negation, after an `E* A*` prefix |
| Notation | `Es_a^{<=k}.` and `(a, s_a)` | `E{k}s:` and `(s, a)` |
| Boolean functions | Any `f` on truth values (the paper uses true, `max` and `-x`) | None inside a goal |
| Quantifier alternation | Arbitrary | Two blocks, existential then universal |
| Precedence and quantifier scope | Not stated (as in `Es. phi U psi`) | Not needed: a goal has one operator |
| Out of scope | Arbitrary Strategy Logic | No support for arbitrary LTL objectives, recall strategies or epistemic guards; such input fails the prefix or goal checks |

## Code map

Table 2 lists the files of the checker and their role; paths are relative to
`model_checker/`.

**Table 2: NatSL code map.**

| Path | Role |
| :--- | :--- |
| `algorithms/explicit/NatSL/core.py` | Entry and shared bounded-strategy model-checking core |
| `parsers/formulas/NatSL/parser.py` | Formula parser |

## Tests

Paths are relative to `model_checker/`:

- `tests/integration/algorithms/natsl/`: semantic regression tests.
- `tests/unit/parsers/formulas/test_natsl_parser.py`: parser tests.
- `tests/fixtures/CGS/NatSL/`: NatSL CGS fixtures.
- Scalability experiments are in `experiments/natsl/` (see [experiments.md](../examples/natsl_experiments.md)).
