# NatATL algorithm reference

This page covers the denotations and code path of the NatATL checker in
`model_checker/algorithms/explicit/NatATL/`, for a developer reading or changing
it; the syntax is in the [syntax cards](../logic_knowledge_base.md#syntax-cards)
and the model file format in [CGS sections](../file_formats.md#cgs-sections).

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

NatATL has two variants, listed in Table 1.

**Table 1: NatATL variants.**

| Variant | Path | Meaning |
| :--- | :--- | :--- |
| Memoryless | `NatATL/Memoryless/` | Strategies depend on current state |
| Recall | `NatATL/Recall/` | History-dependent strategies |

The logic name `NatATL` selects the memoryless solver and `NatATL_Recall` the recall
solver (`NatATL/Recall/natatl_recall.py`). NatATLF has its own page,
[NatATLF](../NatATLF/algorithm.md).

Return contract: a dict with boolean `Satisfiability`, `Complexity Bound` (the
smallest bound at which a strategy was found, or the formula's bound `k` when none
was), `Winning Strategy per agent` (only
when satisfied), and the text fields `res` and `initial_state`. There is no
CTL-style winning-set report.

Implementation techniques (strategy pruning, condition cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

Table 2 sets the usual theory beside this implementation.

**Table 2: NatATL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Bound `k` | Strategy complexity | Condition-token depth |
| Memory models | Memoryless / recall | Separate algorithm packages |
| NatATLF | Related fixed-point flavor | Separate logic package, delegates to memoryless |

## Model-checking pipeline

```text
CGS.read_file -> NatATLParser.parse -> strategy synthesis / pruning
  -> verification result
```

## Code map

Table 3 lists the files of the checker and their role.

**Table 3: NatATL code map.**

| Path | Role |
| :--- | :--- |
| `NatATL/Memoryless/` | Memoryless solver |
| `NatATL/Recall/` | Recall solver and tree helpers |
| `NatATL/natatl_ast.py` | Shared AST helpers |
| `NatATL/NatATLtoCTL.py` | Formula to CTL text and coalition extraction |

## Tests

NatATL fixtures and integration tests under `model_checker/tests/`.
