# CTL algorithm reference

This page covers the denotations and code path of the CTL checker in
`model_checker/algorithms/explicit/CTL/`, for a developer reading or changing it;
the logic is described in the
[knowledge base](../reference/logic_knowledge_base.md#ctl---computation-tree-logic) and the
model file format in [CGS sections](../reference/file_formats.md#cgs-sections).

## Model

- Type: `CGS`
- Signature: finite states `S`, serial transition relation, labelling `V`,
  agents for game structure (CTL ignores coalitions in formulas)

## Formula language

Parser: `parsers/formulas/CTL/parser.py`

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi
      | E X phi | A X phi | E F phi | A F phi | E G phi | A G phi
      | E [phi U psi] | A [phi U psi] | E (phi U psi) | A (phi U psi)
      | E phi U psi | A phi U psi
```

Every temporal operator must be prefixed by `E` or `A`. The three Until forms
above build one tree. Square brackets appear only around an Until, and
parentheses group everything else, so `[p] && q` is a syntax error (see
[grouping](../reference/logic_knowledge_base.md#boolean-logic-shared-syntax) for the
source). A connective after a prefix that no parenthesis closes, as in
`AF p && q`, is a syntax error too (see
[the knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

Each subformula `phi` is labelled bottom-up with `[[phi]]`, the set of states
where it holds. `R` is the transition relation of the CGS; `Pre_exists(X)` is the
set of R-predecessors of `X`, and `Pre_forall(X)` the set of states whose
R-successors are all in `X`. Table 1 gives the denotation of each operator.

**Table 1: CTL operator denotations.**

| Operator | Shape |
| :--- | :--- |
| `EX phi` | `Pre_exists([[phi]])` |
| `AX phi` | `Pre_forall([[phi]])` |
| `EF phi` | least fixpoint under `Pre_exists` from `[[phi]]` |
| `EG phi` | greatest fixpoint under `Pre_exists` intersect `[[phi]]` |
| `AF` / `AG` / `EU` / `AU` | Standard CTL fixpoints (see `operators.py`) |

Implementation techniques (performance tests): [algorithm design](index.md).

## Theory vs implementation

Table 2 sets the usual theory beside this implementation.

**Table 2: CTL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Release operator (`A(p R q)`) | In many textbook CTL definitions | Not in the grammar; `A(p R q)` is a syntax error |
| Witness / counterexample | A path that shows why the formula holds or fails, as the path to a state where `f` fails for `AG f` (Clarke, Emerson and Sistla, ACM TOPLAS 8(2), 1986) | With `generate_trace=True`, one path for the root operator only: a witness when an `E` root holds, a counterexample when an `A` root fails. No trace for a false `E` root or a true `A` root, a boolean or atom root, or a path over 100 states (`MAX_TRACE_LENGTH`) |
| Model | Kripke / transition system | CGS used as transition system |

## Code map

Table 3 lists the files of the checker and their role.

**Table 3: CTL code map.**

| Path | Role |
| :--- | :--- |
| `CTL/CTL.py` | Entry, result / trace |
| `CTL/solver.py` | Dispatch |
| `CTL/operators.py` | Denotations |
| `CTL/traces.py` | Trace of the root operator |
| `CTL/preimage.py` | `Pre_exists` / `Pre_forall` |

## Tests

Integration and unit coverage under `model_checker/tests/` for CTL parsers and
explicit algorithms (fixtures under `tests/fixtures/CGS/`). Traces:
`model_checker/tests/integration/algorithms/ctl/test_traces.py`.
