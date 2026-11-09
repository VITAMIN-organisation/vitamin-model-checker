# CTL - Algorithm Reference

Scope: denotations and code path for CTL in
`model_checker/algorithms/explicit/CTL/`. 

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
[grouping](../logic_knowledge_base.md#boolean-logic-shared-syntax) for the
source). A connective after a prefix that no parenthesis closes, as in
`AF p && q`, is a syntax error too (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

Bottom-up labelling of `[[phi]] subseteq S` using R-predecessors on the CGS
transition graph.

| Operator | Shape |
|---|---|
| `EX phi` | `Pre_exists([[phi]])` |
| `AX phi` | `Pre_forall([[phi]])` |
| `EF phi` | least fixpoint under `Pre_exists` from `[[phi]]` |
| `EG phi` | greatest fixpoint under `Pre_exists` intersect `[[phi]]` |
| `AF` / `AG` / `EU` / `AU` | Standard CTL fixpoints (see `operators.py`) |

Optional traces (`generate_trace=True`) are reachability hints into/out of the
denotation, not full CTL path witnesses.

Implementation techniques (trace edge reuse, performance tests): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Release | Often present | Surface sugar via duals; see operators |
| Traces | Path witness / counterexample | Shortest-path style hint only |
| Model | Kripke / transition system | CGS used as transition system |

## Model-checking pipeline

```text
CGS.read_file -> CTLParser.parse -> build_tree -> solve_tree
  -> format_model_checking_result (+ optional trace)
```

Entry: `CTL/CTL.py` (`model_checking`).

## Code map

| Path | Role |
|---|---|
| `CTL/CTL.py` | Entry, result / trace |
| `CTL/solver.py` | Dispatch |
| `CTL/operators.py` | Denotations |
| `CTL/operators_with_trace.py` | Trace-enabled handlers |
| `CTL/preimage.py` | `Pre_exists` / `Pre_forall` |

## Tests

Integration and unit coverage under `model_checker/tests/` for CTL parsers and
explicit algorithms (fixtures under `tests/fixtures/CGS/`).
