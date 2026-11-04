# COTL - Algorithm Reference

Scope: denotations and code path for COTL in
`model_checker/algorithms/explicit/COTL/`. 
## Model

- Type: `costCGS`
- Same model family as OATL; different checker.

## Formula language

Parser: `parsers/formulas/COTL/parser.py`

```text
phi ::= ... | <A><k> X phi | <A><k> F phi | <A><k> G phi
           | <A><k>(phi U psi) | <A><k>(phi R psi) | <A><k>(phi W psi)
```

Coalition and bound: `<1,2><5>`. `R` and `W` are accepted and implemented here.

## Semantic denotations

Cost-bounded coalition strategy synthesis via dedicated least / greatest
fixpoints in `COTL/`, independent of the OATL checker.

Implementation techniques (cost caches + reset, `pre_by_index`, bit-vector): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Syntax | `<A><k>` | `<1,2><5>` (coalition then bound) |
| Engine | Cost-bounded ATL | Dedicated COTL fixpoints |
| R / W | Present | Implemented |

## Model-checking pipeline

```text
costCGS.read_file -> COTLParser.parse -> build_tree -> COTL solve_tree -> result
```

Entry: `COTL/COTL.py`.

## Code map

| Path | Role |
|---|---|
| `COTL/COTL.py` | Entry |
| `COTL/solver.py` | Dispatch |
| `COTL/operators.py` | Fixpoint operators |
| `COTL/preimage.py` | Cost-aware pre-image |

## Tests

COTL fixtures under costCGS / algorithm tests.
