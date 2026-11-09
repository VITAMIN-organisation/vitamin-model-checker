# NatATL - Algorithm Reference

Scope: denotations and code path for NatATL in
`model_checker/algorithms/explicit/NatATL/`.

## Model

- Type: `CGS`
- Bound `k` limits strategy complexity (condition-token depth), not coalition size.

## Formula language

Parser: `parsers/formulas/NatATL/parser.py`

```text
phi ::= ... | <{A}, k> X phi | <{A}, k> F phi | <{A}, k> G phi | <{A}, k>(phi U psi)
```

Braces around agents and a positive integer `k` are required. `k = 0` is rejected with
an error that names the value.

## Semantic denotations

Variants:

| Variant | Path | Meaning |
|---|---|---|
| Memoryless | `NatATL/Memoryless/` | Strategies depend on current state |
| Recall | `NatATL/Recall/` | History-dependent strategies |
| Recall Filter | Recall path | Same recall check; ATL conversion may run for diagnostics |

Return contract: boolean `Satisfiability` plus `res` / `initial_state` (not a
full CTL-style winning-set report).

Implementation techniques (strategy pruning, condition cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Bound `k` | Strategy complexity | Condition-token depth |
| Memory models | Memoryless / recall | Separate algorithm packages |
| NatATLF | Related fixed-point flavor | Separate logic package, delegates to memoryless |

## Model-checking pipeline

```text
CGS.read_file -> NatATLParser.parse -> strategy synthesis / pruning
  -> verification result
```

## Code map

| Path | Role |
|---|---|
| `NatATL/Memoryless/` | Memoryless solver |
| `NatATL/Recall/` | Recall solver and tree helpers |
| `NatATL/natatl_ast.py` | Shared AST helpers |

## Tests

NatATL fixtures and integration tests under `model_checker/tests/`.
