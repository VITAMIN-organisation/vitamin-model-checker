# RBATL - Algorithm Reference

Scope: denotations and code path for RBATL in
`model_checker/algorithms/explicit/RBATL/`.

## Model

- Type: `costCGS`
- Flat action costs: `Costs_for_actions` (`agent$cost:cost` style entries).

## Formula language

Parser: `parsers/formulas/RBATL/parser.py`

```text
phi ::= ... | <A><b1,b2,...> X phi | <A><b1,...> F phi | ...
```

Vector bounds are comma-separated. `R` / `W` rejected at parse time.

`<A><b> phi U psi` and `<A><b> (phi U psi)` build the same tree (see
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)), and
`<A><b>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

On each coalition-controlled transition, resource `i` must satisfy
`cost_i <= b_i` (per-step affordability, not cumulative path totals).

Shares the bounded ATL solver pattern (`shared/bounded_atl_solver.py`) with
RABATL; cost derivation differs.

Implementation techniques (transition cache, bit-vector, AST memo, ATL prefilter): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Bounds | Resource vector | `<10,5>` second bracket group |
| Costs | Flat action costs | `Costs_for_actions` |
| Engine | Resource-bounded ATL | Shared bounded ATL solver |

## Model-checking pipeline

```text
costCGS.read_file -> RBATLParser.parse -> bounded ATL solve -> result
```

Entry: `RBATL/RBATL.py`.

## Code map

| Path | Role |
|---|---|
| `RBATL/RBATL.py` | Entry |
| `RBATL/preimage.py` | Cost vector pre-image |
| `shared/bounded_atl_solver.py` | Shared solve path |

## Tests

RBATL fixtures under costCGS / algorithm tests.
