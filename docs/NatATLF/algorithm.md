# NatATLF algorithm reference

This page covers the denotations and code path of the NatATLF checker in
`model_checker/algorithms/explicit/NatATLF/`, for a developer reading or changing
it; the syntax is in the [syntax cards](../logic_knowledge_base.md#syntax-cards)
and the model file format in [CGS sections](../file_formats.md#cgs-sections).

## Model

- Type: `CGS`
- Same models as NatATL.

## Formula language

Parser: `parsers/formulas/NatATLF/parser.py`

Same surface family as NatATL:

```text
<{A}, k> F goal
```

## Semantic denotations

NatATLF uses NatATL-like syntax and delegates checking to the memoryless NatATL
solver path. Report shape matches NatATL memoryless (`Satisfiability`, `res`,
`initial_state`).

Implementation techniques (delegates to NatATL memoryless design): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

Table 1 sets the usual theory beside this implementation.

**Table 1: NatATLF theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Relation to NatATL | Fixed-point / related flavor | Delegates to memoryless NatATL |
| Syntax | `<{A}, k>` | Shared with NatATL |

## Model-checking pipeline

```text
CGS.read_file -> NatATLFParser.parse -> NatATL memoryless path -> result
```

Entry: `NatATLF/NatATL.py`.

## Code map

Table 2 lists the files of the checker and their role.

**Table 2: NatATLF code map.**

| Path | Role |
| :--- | :--- |
| `NatATLF/NatATL.py` | Entry / delegation |

## Tests

Shared NatATL / NatATLF coverage under `model_checker/tests/`.
