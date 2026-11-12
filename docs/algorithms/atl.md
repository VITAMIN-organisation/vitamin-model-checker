# ATL algorithm reference

This page covers the denotations and code path of the ATL checker in
`model_checker/algorithms/explicit/ATL/`, for a developer reading or changing it;
the syntax is in the [syntax cards](../reference/logic_knowledge_base.md#syntax-cards) and
the model file format in [CGS sections](../reference/file_formats.md#cgs-sections).

## Model

- Type: `CGS`
- Signature: states `S`, joint-action transitions, labelling `V`, `Number_of_agents`

## Formula language

Parser: `parsers/formulas/ATL/parser.py`

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi
      | <A> X phi | <A> F phi | <A> G phi | <A>(phi U psi) | <A> phi U psi
```

`<A>(phi U psi)` and `<A> phi U psi` build the same tree (see
[until after a prefix](../reference/logic_knowledge_base.md#until-after-a-prefix)); a connective
after the unparenthesised form is a syntax error (see
[prefix before a connective](../reference/logic_knowledge_base.md#prefix-before-a-connective)).

Coalition form: `<1>`, `<1,2>`. Empty `<>` is rejected. Agent ids must be in `1..n`.

## Semantic denotations

Table 1 gives the denotation of each operator: a coalition pre-image (existential
strategy step), then fixpoints.

**Table 1: ATL operator denotations.**

| Operator | Shape |
| :--- | :--- |
| `<A> X phi` | Coalition exists-move pre-image of `[[phi]]` |
| `<A> F phi` | least fixpoint: grow from `[[phi]]` under that pre-image |
| `<A> G phi` | greatest fixpoint: shrink under pre-image intersect `[[phi]]` |
| `<A>(phi U psi)` | least fixpoint until form |

Implementation techniques (transition cache, bit-vector sets, early-stop,
performance tests): [algorithm design](index.md).

## Theory vs implementation

Table 2 sets the usual theory beside this implementation.

**Table 2: ATL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Coalition | Often `<{1,2}>` | `<1,2>` (no braces) |
| Release / weak | Sometimes present | Not in ATL surface here |
| Empty coalition | Literature may allow | Rejected |

## Code map

Table 3 lists the files of the checker and their role.

**Table 3: ATL code map.**

| Path | Role |
| :--- | :--- |
| `ATL/ATL.py` | Entry |
| `ATL/solver.py` | Dispatch |
| `ATL/operators.py` | Coalition handlers |
| `ATL/preimage.py` | `pre()`, transition cache hook |
| `shared/bit_vector.py` | Shared bit-vector sets (see design page) |

## Tests

- Integration fixtures under `model_checker/tests/fixtures/CGS/`
- Performance regression: `tests/performance/test_atl_performance.py` (100-200
  states, time bounds, fixpoint convergence)
