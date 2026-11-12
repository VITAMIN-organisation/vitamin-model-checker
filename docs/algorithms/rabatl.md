# RABATL algorithm reference

This page gives the denotations and code path of RABATL in
`model_checker/algorithms/explicit/RABATL/`, for developers reading or changing
the checker; the syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl) and the model format
in [costCGS sections](../reference/file_formats.md#costcgs-sections).

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

Each bound value is between 1 and 1000000; the rules are in
[the knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl).

## Semantic denotations

Same per-step vector affordability check as RBATL, with different cost
aggregation from the model. Winning sets can differ from RBATL on the same
formula when split sums disagree with flat costs.

Not a separate recursive-modality engine: shares `bounded_atl_solver` with
RBATL.

Implementation techniques (shared with RBATL: transition cache, bit-vector, AST memo): [algorithm design](index.md).

## Theory vs implementation

Table 1 sets the theory next to what the code does:

**Table 1: RABATL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Costs | Split / coalition-sum | `Costs_for_actions_split` |
| Syntax | Vector bounds | Same as RBATL |
| Engine | Related resource ATL | Shared bounded ATL solver |

## Code map

Table 2 lists the files RABATL runs; paths are relative to
`model_checker/algorithms/explicit/`.

**Table 2: RABATL code map.**

| Path | Role |
| :--- | :--- |
| `RABATL/RABATL.py` | Entry |
| `RABATL/preimage.py` | Split-cost pre-image |
| `shared/bounded_atl_solver.py` | Shared solve path |

## Tests

RABATL fixtures under costCGS / algorithm tests.
