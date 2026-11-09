# CapATL - Algorithm Reference

Scope: denotations and code path for CapATL in
`model_checker/algorithms/explicit/CapATL/`. 

## Model

- Type: `capCGS`
- Capacities constrain available actions via model sections, not a numeric
  formula bound `k`.

## Formula language

Parser: `parsers/formulas/CapATL/parser.py`

```text
phi ::= ... | <{A}> X phi | <{A}> F phi | <{A}> G phi | <{A}> phi U psi
           | <{A}> (phi U psi) | <{A}> phi R psi | <{A}> (phi R psi)
           | Ki(phi) | i is prop   -- grammar forms; see theory vs impl
```

`<{A}> phi U psi` and `<{A}> (phi U psi)` build the same tree, and so do the two
forms of `R` (see
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)).
`<{A}>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

Formula bound `<{A}, k>` is rejected (no numeric `k` in CapATL). `W` is
unsupported.

## Semantic denotations

Coalition modalities over capacity-restricted transitions. Release uses a
greatest fixpoint in the CapATL solver. Knowledge forms `Ki` and agent-scoped
`i is p` appear in the grammar but are not fully wired through the bottom-up
solver yet; prefer temporal goals over model atoms until that path is complete.

Implementation techniques (lru caches + clear, state index cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Coalition | `<{A}>` | Braces required; no formula `k` |
| `Ki` / `i is p` | Knowledge / agent props | Parsed; not fully evaluated yet |
| Capacities | Model constraints | `capCGS` sections + Pre over capacity knowledge |

## Model-checking pipeline

```text
capCGS.read_file -> CapATLParser.parse -> build_tree -> solve_tree -> result
```

Entry: `CapATL/CapATL.py`.

## Code map

| Path | Role |
|---|---|
| `CapATL/CapATL.py` | Entry |
| `CapATL/solver.py` | Dispatch |
| `CapATL/operators.py` | Operators |
| `CapATL/preimage.py` | Pre-image |
| `CapATL/knowledge.py` | Knowledge helpers |

## Tests

CapATL fixtures under capCGS / algorithm tests.
