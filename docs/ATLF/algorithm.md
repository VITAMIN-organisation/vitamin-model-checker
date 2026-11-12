# ATLF algorithm reference

This page covers the denotations and code path of the ATLF checker in
`model_checker/algorithms/explicit/ATLF/`, for a developer reading or changing it;
the syntax is in the [syntax cards](../logic_knowledge_base.md#syntax-cards) and
the model file format in [CGS sections](../file_formats.md#cgs-sections).

## Model

- Type: `CGS`
- Same game structure as ATL; evaluation uses the ATLF fixed-point engine.

## Formula language

Parser: `parsers/formulas/ATLF/parser.py`

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi
      | <A> X phi | <A> F phi | <A> G phi | <A>(phi U psi) | <A> phi U psi
```

Coalition form matches ATL: `<1>`, `<1,2>`. `<A>(phi U psi)` and `<A> phi U psi`
build the same tree (see
[until after a prefix](../logic_knowledge_base.md#until-after-a-prefix)); a connective
after the unparenthesised form is a syntax error (see
[prefix before a connective](../logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

ATLF gives each state a number, not a yes or no. An atom's value in a state is its
cell in the labelling matrix, read as a float (`get_tuple_list_prop` in `ATLF/ATLF.py`).
The connectives combine values state by state (`ATLF/operators.py`,
`ATLF/real_value_utils.py`), as Table 1 shows.

**Table 1: ATLF connective values.**

| Formula | Value in state `s` |
| :--- | :--- |
| `!phi` | `1 - phi(s)` |
| `phi && psi` | `min(phi(s), psi(s))` |
| `phi \|\| psi` | `max(phi(s), psi(s))` |

Coalition modalities are fixed points over these values (`ATLF/preimage.py`). The
result is a list of `(state, value)` pairs, and the `initial_state` field is a text
line with the value at the initial state, such as `Initial state s0: 0.0`.

Implementation techniques (per-operator transition cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

Table 2 sets the usual theory beside this implementation.

**Table 2: ATLF theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Valuation | Often real-valued / fixed-point ATL | ATLF engine over CGS |
| Syntax | ATL-like coalitions | Same surface family as ATL |

## Model-checking pipeline

```text
CGS.read_file -> ATLFParser.parse -> build_resolved_formula_tree -> solve_tree -> result
```

Entry: `ATLF/ATLF.py`.

## Code map

Table 3 lists the files of the checker and their role.

**Table 3: ATLF code map.**

| Path | Role |
| :--- | :--- |
| `ATLF/ATLF.py` | Entry |
| `ATLF/solver.py` | Dispatch |
| `ATLF/operators.py` | Operators |
| `ATLF/preimage.py` | Pre-image |
| `ATLF/real_value_utils.py` | Real-valued helpers |

## Tests

ATLF coverage under `model_checker/tests/` (parser and algorithm suites).
