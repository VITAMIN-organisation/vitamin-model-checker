# RBATL algorithm reference

This page gives the denotations and code path of RBATL in
`model_checker/algorithms/explicit/RBATL/`, for developers reading or changing
the checker; the syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl) and the model format
in [costCGS sections](../reference/file_formats.md#costcgs-sections).

## Model

- Type: `costCGS`
- Flat action costs: `Costs_for_actions`, one line per joint action as
  `action state$cost[:cost...]`, several states joined by `;` (see
  [costCGS sections](../reference/file_formats.md#costcgs-sections)).

## Formula language

Parser: `parsers/formulas/RBATL/parser.py`

```text
phi ::= ... | <A><b1,b2,...> X phi | <A><b1,...> F phi | ...
```

Vector bounds are comma-separated. `R` / `W` rejected at parse time. Each bound value
is between 1 and 1000000; the rules are in
[the knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl).

`<A><b> phi U psi` and `<A><b> (phi U psi)` build the same tree (see
[the knowledge base](../reference/logic_knowledge_base.md#until-after-a-prefix)), and
`<A><b>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

On each coalition-controlled transition, resource `i` must satisfy
`cost_i <= b_i` (per-step affordability, not cumulative path totals).

Shares the bounded ATL solver pattern (`shared/bounded_atl_solver.py`) with
RABATL; cost derivation differs.

Implementation techniques (transition cache, bit-vector, AST memo): [algorithm design](index.md).

## Theory vs implementation

Table 1 sets the theory next to what the code does:

**Table 1: RBATL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Bounds | Resource vector | `<10,5>` second bracket group |
| Costs | Flat action costs | `Costs_for_actions` |
| Engine | Resource-bounded ATL | Shared bounded ATL solver |

## Code map

Table 2 lists the files RBATL runs; paths are relative to
`model_checker/algorithms/explicit/`.

**Table 2: RBATL code map.**

| Path | Role |
| :--- | :--- |
| `RBATL/RBATL.py` | Entry |
| `RBATL/preimage.py` | Cost vector pre-image |
| `shared/bounded_atl_solver.py` | Shared solve path |

## Tests

RBATL fixtures under costCGS / algorithm tests.
