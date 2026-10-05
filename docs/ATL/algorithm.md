# ATL - Algorithm Reference

Scope: denotations and code path for ATL in `model_checker/algorithms/explicit/ATL/`.

## Model

- Type: `CGS`
- Signature: states `S`, joint-action transitions, labelling `V`, `Number_of_agents`

## Formula language

Parser: `parsers/formulas/ATL/parser.py`

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi
      | <A> X phi | <A> F phi | <A> G phi | <A>(phi U psi)
```

Coalition form: `<1>`, `<1,2>`. Empty `<>` is rejected. Agent ids must be in `1..n`.

## Semantic denotations

Coalition pre-image (existential strategy step), then fixpoints:

| Operator | Shape |
|---|---|
| `<A> X phi` | Coalition exists-move pre-image of `[[phi]]` |
| `<A> F phi` | least fixpoint: grow from `[[phi]]` under that pre-image |
| `<A> G phi` | greatest fixpoint: shrink under pre-image intersect `[[phi]]` |
| `<A>(phi U psi)` | least fixpoint until form |

Implementation techniques (transition cache, bit-vector sets, early-stop,
performance tests): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Coalition | Often `<{1,2}>` | `<1,2>` (no braces) |
| Release / weak | Sometimes present | Not in ATL surface here |
| Empty coalition | Literature may allow | Rejected |

## Model-checking pipeline

```text
CGS.read_file -> ATLParser.parse -> build_tree -> build_transition_cache
  -> solve_tree -> format_model_checking_result
```

Entry: `ATL/ATL.py` via `create_model_checking_entry`.

## Code map

| Path | Role |
|---|---|
| `ATL/ATL.py` | Entry |
| `ATL/solver.py` | Dispatch |
| `ATL/operators.py` | Coalition handlers |
| `ATL/preimage.py` | `pre()`, transition cache hook |
| `shared/bit_vector.py` | Shared bit-vector sets (see design page) |

## Tests

- Integration fixtures under `model_checker/tests/fixtures/CGS/`
- Performance regression: `tests/performance/test_atl_performance.py` (100-200
  states, time bounds, fixpoint convergence)
