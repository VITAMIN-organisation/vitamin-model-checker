# OATL - Algorithm Reference

Scope: semantics and code path for OATL in
`model_checker/algorithms/explicit/OATL/`, following D. Catta, J. Leneutre,
V. Malvone, A. Murano, "Obstruction Alternating-time Temporal Logic: a Strategic
Logic to Reason about Dynamic Models", AAMAS 2024. Syntax and examples are in
the [knowledge base](../logic_knowledge_base.md#oatl).

## Model

- Type: `costCGS`.
- A `Costs_for_actions` entry `$(s, a)` is what the Demon pays to erase joint
  action `a` at state `s`. A cost vector is summed into one number.
- A joint action may have no cost. The check fails, naming the formula, the
  states and the uncosted actions, only when the answer depends on those costs:
  each fixpoint is computed with missing costs at +inf and at 0, and the two
  results must agree. A missing cost is never silently treated as 0.

## Formula language

Parser: `parsers/formulas/OATL/parser.py`

```text
phi ::= p | true | false | !phi | phi && phi | phi || phi | phi -> phi
      | <A><n> X phi | <A><n> F phi | <A><n> G phi
      | <A><n> (phi U psi) | <A><n> (phi R psi) | <A><n> (phi W psi)
```

`<A><n>` is the paper's `[[A]]_n`. The budget `n` is mandatory and `n >= 0`,
as in the paper; with `n = 0` the Demon can erase only zero-cost joint actions.
The parentheses around a binary operator are optional: `<A><n> phi U psi`
parses the same way.

## Semantics

`<A><n> theta` holds at `s` when the Demon has a strategy that, at each step,
erases joint actions of total cost at most `n` (never all of them), so that for
every strategy of coalition `A` some remaining path satisfies `theta`. Agents
outside `A` resolve the remaining choices in the Demon's favour. The budget
applies to each step on its own; it is not a sum along the path.

## Algorithm

One step is the demonic pre-image `Pre_n(A, X)` (Proposition 1). An A-action
`f` at `s` is the coalition's part of a joint action; `next(f, s)` is the set
of states its joint actions lead to. Then `s` is in `Pre_n(A, X)` when:

1. some transition from `s` enters `X`, and
2. the joint actions of every A-action `f` with `next(f, s)` disjoint from `X`
   (the set `D(s, A, X)`) cost at most `n` in total.

The Demon has to erase exactly `D(s, A, X)`: an A-action that cannot reach `X`
must lose all its joint actions, and any other A-action keeps a path into `X`.
The formal definition of `D` in the paper writes `next(f, s)` included in `X`;
the text after it and the proof of Proposition 1 use the complement, which is
what is implemented.

The temporal operators are fixpoints of `Pre_n` (Theorem 1):

| Formula | Fixpoint |
| :--- | :--- |
| `<A><n> X phi` | `Pre_n(A, phi)` |
| `<A><n> phi U psi` | least `T = psi \| (phi & Pre_n(A, T))` |
| `<A><n> phi R psi` | greatest `T = psi & (phi \| Pre_n(A, T))` |
| `<A><n> F phi` | least `T = phi \| Pre_n(A, T)` |
| `<A><n> G phi` | greatest `T = phi & Pre_n(A, T)` |
| `<A><n> phi W psi` | greatest `T = (phi \| psi) & (psi \| Pre_n(A, T))` |

Here `|` is union and `&` is intersection of state sets.

`DemonicPreimage` expands every transition cell once per check, groups the
joint actions of each state by the coalition's part, and sums each group's
cost. Each `Pre_n` call is then one pass over these groups, so a fixpoint costs
at most `|S|` passes over the transitions.

There is no ATL prefilter: `<A><n> phi` does not imply ATL `<A> phi`, because
the agents outside `A` side with the Demon.

## Model-checking pipeline

```text
costCGS.read_file -> OATLParser.parse -> build_resolved_formula_tree
  -> solve_tree (DemonicPreimage + fixpoints) -> result
```

Entry: `OATL/OATL.py`.

## Code map

| Path | Role |
| :--- | :--- |
| `OATL/OATL.py` | Entry, costCGS check |
| `OATL/solver.py` | Operator dispatch |
| `OATL/operators.py` | X, F, G, U, R, W fixpoints |
| `OATL/preimage.py` | Demonic pre-image `Pre_n(A, X)` |

OATL shares no pre-image code with COTL.

## Tests

`tests/integration/algorithms/oatl/test_correctness.py`:

- Least budget that blocks the attack is 3: on the attack model of Section 3 of
  the paper (`fixtures/costCGS/OATL/oatl_3agents_medium_6states_costs.txt`),
  `<1,2><n> G !(r && s && g)` fails at `s0` for `n = 2` and holds for `n = 3`,
  also in the `false R` and parenthesised forms.
- The Demon pays the sum over every A-action that misses the target.
- Budget 0 erases only zero-cost moves.
- Agents outside the coalition side with the Demon.
- `U` is a least fixpoint and `W` a greatest one.
- A missing cost that decides the result is an error; one that cannot change
  it is ignored.
