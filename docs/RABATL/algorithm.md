# RABATL - Algorithm Reference

Scope: denotations and code path for RABATL in
`model_checker/algorithms/explicit/RABATL/`.

## Model

- Type: `costCGS` with split costs
- Uses `Costs_for_actions_split` and sums coalition members' cost components
  on joint actions.

## Formula language

Parser: `parsers/formulas/RABATL/parser.py`

Same surface as RBATL:

```text
<1,2><10,5> F goal
```

## Semantic denotations

Same per-step vector affordability check as RBATL, with different cost
aggregation from the model. Winning sets can differ from RBATL on the same
formula when split sums disagree with flat costs.

Not a separate recursive-modality engine: shares `bounded_atl_solver` with
RBATL.

Implementation techniques (shared with RBATL: transition cache, bit-vector, AST memo): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Costs | Split / coalition-sum | `Costs_for_actions_split` |
| Syntax | Vector bounds | Same as RBATL |
| Engine | Related resource ATL | Shared bounded ATL solver |

## Model-checking pipeline

```text
costCGS.read_file -> RABATLParser.parse -> bounded ATL solve -> result
```

Entry: `RABATL/RABATL.py`.

## Code map

| Path | Role |
|---|---|
| `RABATL/RABATL.py` | Entry |
| `RABATL/preimage.py` | Split-cost pre-image |
| `shared/bounded_atl_solver.py` | Shared solve path |

## Tests

RABATL fixtures under costCGS / algorithm tests.
