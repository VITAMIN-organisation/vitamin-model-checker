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

Implementation techniques (performance tests): [algorithm_design.md](../algorithm_design.md).

## Traces

With `generate_trace=True` the result is the full dict (`res`, `initial_state`,
`satisfied`, `states`, `trace`, `strategy`, `metadata`). Its `trace` explains
the root operator, which is the outermost operator of the formula, at the
initial state (`s0` below). A witness is a path that shows why an E-operator
(one that starts with the path quantifier `E`) holds. A counterexample is a path
that shows why an A-operator (one that starts with `A`) fails: the negation of
its path formula holds on that path. A lasso is a path that ends in a loop.
E. M. Clarke, E. A. Emerson and A. P. Sistla describe the same counterexample
for `AG f`, a path to a state where `f` fails ("Automatic Verification of
Finite-State Concurrent Systems Using Temporal Logic Specifications", ACM TOPLAS
8(2), 1986, `docs/papers/CES86.pdf`, p. 256).

| Root operator | At `s0` | Trace |
|---|---|---|
| `EX phi` | true | witness: `s0` and a successor in `[[phi]]` |
| `EF phi` | true | witness: a shortest path that ends in `[[phi]]` (`s0` alone when `s0` is in `[[phi]]`) |
| `E[phi U psi]` | true | witness: a shortest path that ends in `[[psi]]`, with every earlier state in `[[phi]]` |
| `EG phi` | true | witness: a lasso inside `[[EG phi]]` |
| `AX phi` | false | counterexample: `s0` and a successor outside `[[phi]]` |
| `AG phi` | false | counterexample: a shortest path that ends outside `[[phi]]` |
| `AF phi` | false | counterexample: a lasso outside `[[AF phi]]`, so `phi` never holds on it |
| `A[phi U psi]` | false | counterexample: a shortest path through states outside `[[psi]]` to a state outside both `[[phi]]` and `[[psi]]`; when there is none, a lasso outside `[[A[phi U psi]]]`, on which `psi` never holds |

`trace` is a dict with the keys `states`, `type` (`witness` or
`counterexample`), `description`, `length` and `cycle_start_index`. For a lasso,
`trace["states"]` lists each state once and `trace["cycle_start_index"]` is the
index that the last state steps back to. For a finite path
`trace["cycle_start_index"]` is `None` (`null` in JSON). For `EG (p || q)` on
`model_checker/tests/fixtures/CGS/ATL/atl_2agents_4states_simple.txt` the trace
has the states `[s0, s1, s3]` and the index 2, which stands for the path
`s0 s1 s3 s3 ...`.

These cases have no trace, and `trace` is `None`:

- A false E-operator or a true A-operator: the verdict is about every path from
  `s0`, so no single path shows it.
- A root that is a boolean connective or an atom, such as `!AG p` or
  `(EF p) && (EG q)`: not supported.
- A path or lasso of more than 100 states (`MAX_TRACE_LENGTH` in
  `shared/trace_utils.py`): the result has no trace instead of a truncated one.

The trace explains the root operator only. For `EF (AG p)` it is a path to a
state in `[[AG p]]`, and it does not show why `AG p` holds there.

The lasso stays inside the set named in the table and has the fewest states of
any lasso there. Its entry state is where the path from `s0` meets the loop. The
checker finds the states on a cycle inside the set (a self-loop counts) with
Tarjan's algorithm for strongly connected components, and tries each as the
entry in order of distance from `s0`: a shortest path to it, then a shortest
cycle through it. It keeps the entry with the fewest states in total, because a
farther entry can have a shorter loop.

Each cycle search skips lassos longer than the best one found so far, or longer
than 100 states before one is found. When no lasso fits, nothing cuts the
searches short: the work is one search per cycle state within 100 steps of
`s0`, which is the slow case on a large model whose cycles all have more than
100 states.

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Release | Often present | Surface sugar via duals; see operators |
| Traces | Path witness / counterexample | For the root operator only; see [Traces](#traces) |
| Model | Kripke / transition system | CGS used as transition system |

## Model-checking pipeline

```text
CGS.read_file -> CTLParser.parse -> build_tree -> solve_tree
  -> VerificationResult.to_compact_dict
  (generate_trace=True: build_trace -> VerificationResult.to_dict)
```

Entry: `CTL/CTL.py` (`model_checking`).

## Code map

| Path | Role |
|---|---|
| `CTL/CTL.py` | Entry, result / trace |
| `CTL/solver.py` | Dispatch |
| `CTL/operators.py` | Denotations |
| `CTL/traces.py` | Trace of the root operator |
| `CTL/preimage.py` | `Pre_exists` / `Pre_forall` |

## Tests

Integration and unit coverage under `model_checker/tests/` for CTL parsers and
explicit algorithms (fixtures under `tests/fixtures/CGS/`). Traces:
`model_checker/tests/integration/algorithms/ctl/test_traces.py`.
