# OL - Algorithm Reference

Scope: denotations and code path for OL in
`model_checker/algorithms/explicit/OL/`.

## Model

- Type: `costCGS`
- Linear-time cost-bounded logic paired with OATL models.

## Formula language

Parser: `parsers/formulas/OL/parser.py`

```text
phi ::= ... | <Jk> X phi | <Jk> F phi | <Jk> G phi
           | <Jk>(phi U psi) | <Jk>(phi R psi) | <Jk>(phi W psi)
```

Prefix must include `J` (`<J5>`). Bound `k >= 1`.

## Semantic denotations

| Operator family | Cost meaning |
|---|---|
| `F` / `G` / `U` / `R` / `W` | Accumulated path cost `<= k` |
| `X` | Next transition cost `<= k` |

This differs from OATL, where the budget limits what the Demon erases at each
step, and from TOL (per-position demonic deactivation on timed models).

Shared costCGS techniques: [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Prefix | Demonic / cost bound | `<Jk>` mandatory |
| Path cost | Budget along path | Accumulated for most ops; per-step for `X` |

## Model-checking pipeline

```text
costCGS.read_file -> OLParser.parse -> build_tree -> solve_tree -> result
```

Entry: `OL/OL.py`.

## Code map

| Path | Role |
|---|---|
| `OL/OL.py` | Entry |
| `OL/solver.py` | Dispatch |
| `OL/operators.py` | Operators |
| `OL/preimage.py` | Cost-aware pre-image |

## Tests

OL fixtures and integration tests under `model_checker/tests/`.
