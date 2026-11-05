# OATL - Algorithm Reference

For developers who need to know how OATL is checked in this project. Code is in
`model_checker/algorithms/explicit/OATL/`; the method follows D. Catta, J.
Leneutre, V. Malvone, A. Murano, "Obstruction Alternating-time Temporal Logic:
a Strategic Logic to Reason about Dynamic Models", AAMAS 2024. Syntax and
examples are in the [knowledge base](../logic_knowledge_base.md#oatl).

## Idea

A game between agents and one Demon. The Demon erases joint actions of the
model, at a cost. `<A><n> theta` holds at a state when the Demon, spending at
most `n` per step, can erase actions so that whatever coalition `A` plays, some
remaining path satisfies `theta`.

Notation: `phi` and `psi` are state formulas, `theta` is a path formula such as
`X phi`, and a *joint action* is one action per agent, written as a token such
as `AA^` (agents 1, 2, 3 play `A`, `A`, `^`). Agents are numbered from 1.

## Model

Type `costCGS` ([format](../file_formats.md#costcgs-sections)). An entry of
`Costs_for_actions` is what the Demon pays to erase joint action `a` at state
`s`; a cost vector is summed into one number.

A joint action may have no cost, as the self-loops of the example model. The
check then fails, naming the formula, the states and the actions, only when the
result of a modal subformula at some state, not only the initial one, depends
on those costs. To decide this, each fixpoint is run with missing costs at +inf
and at 0, and the two results must agree. A missing cost is never silently 0.

## Formula language

Parser: `model_checker/parsers/formulas/OATL/parser.py`

```text
phi ::= p | true | false | !phi | phi && phi | phi || phi | phi -> phi
      | <A><n> X phi | <A><n> F phi | <A><n> G phi
      | <A><n> (phi U psi) | <A><n> (phi R psi) | <A><n> (phi W psi)
```

`<A><n>` needs a non-empty coalition `A` and a budget `n >= 0`. With `n = 0`
the Demon erases only zero-cost joint actions. Parentheses around a binary
operator are optional.

## Semantics

At each step the Demon erases joint actions of total cost at most `n`, never
all of them. The budget applies to each step on its own, not to the whole path.
Agents outside `A` play in the Demon's favour. For this reason `<A><n> phi` does
not imply the ATL formula `<A> phi`, and OATL does not use ATL results as a
shortcut.

## Algorithm

Every subformula is evaluated bottom-up to the set of states where it holds.
The formula holds in the model when the initial state is in the final set.

One step is the Demon pre-image `Pre_n(A, S)`, for a set of states `S`. An
*A-action* at a state is the coalition's part of a joint action (for
`A = {1,2}`, the joint action `AA^` gives the A-action `AA`); its successors are
the states its joint actions lead to. A state is in `Pre_n(A, S)` when:

1. some A-action there has a successor in `S`, and
2. the joint actions of all A-actions whose successors miss `S` cost at most
   `n` in total.

The Demon must erase exactly the A-actions that miss `S`: one left in place
could be chosen by `A`, and then all its paths would leave `S`. A state with no
transition is never in `Pre_n`.

Temporal operators are fixpoints of `Pre_n`, where `T` ranges over sets of
states and `|`, `&` are union and intersection. Least fixpoints iterate up from
the starting set, greatest ones down from it.

| Formula | Fixpoint |
| :--- | :--- |
| `<A><n> X phi` | `Pre_n(A, phi)` |
| `<A><n> phi U psi` | least `T = psi \| (phi & Pre_n(A, T))` |
| `<A><n> phi R psi` | greatest `T = psi & (phi \| Pre_n(A, T))` |
| `<A><n> F phi` | least `T = phi \| Pre_n(A, T)` |
| `<A><n> G phi` | greatest `T = phi & Pre_n(A, T)` |
| `<A><n> phi W psi` | greatest `T = (phi \| psi) & (psi \| Pre_n(A, T))` |

`F`, `G` and `W` are implemented directly. They give the same states as
`true U phi`, `false R phi` and `psi R (phi | psi)`.

`DemonicPreimage` expands every transition once per check and groups the joint
actions of each state by the coalition's part. Each `Pre_n` call is one pass
over these groups.

## Example

On the attack model of the paper
([oatl_3agents_medium_6states_costs.txt](../../model_checker/tests/fixtures/costCGS/OATL/oatl_3agents_medium_6states_costs.txt)),
agents 1 and 2 are the attackers and the Demon blocks them:

- `<1,2><2> G !(r && s && g)` is false at `s0`;
- `<1,2><3> G !(r && s && g)` is true at `s0`: 3 is the least budget that
  blocks the attack, as the paper states.

## Pipeline and code

```text
CostCGS.read_file -> OATLParser.parse -> build_resolved_formula_tree
  -> solve_tree (DemonicPreimage + fixpoints) -> result
```

Paths below are relative to `model_checker/algorithms/explicit/`.

| Path | Role |
| :--- | :--- |
| `OATL/OATL.py` | Entry, costCGS check |
| `OATL/solver.py` | Operator dispatch, builds `DemonicPreimage` |
| `OATL/operators.py` | X, F, G, U, R, W fixpoints and the missing-cost check |
| `OATL/preimage.py` | `DemonicPreimage`, the `Pre_n` computation |

## Tests

[test_correctness.py](../../model_checker/tests/integration/algorithms/oatl/test_correctness.py)
covers the budget threshold above, budget 0, the cost sum over A-actions,
agents outside `A`, `U` as least and `W` as greatest fixpoint, and the
missing-cost error.
