# OATL algorithm reference

This page explains how OATL is checked in this project, for developers reading
or changing the checker. Code is in
`model_checker/algorithms/explicit/OATL/`; the method follows D. Catta, J.
Leneutre, V. Malvone, A. Murano, "Obstruction Alternating-time Temporal Logic:
a Strategic Logic to Reason about Dynamic Models", AAMAS 2024. Syntax and
examples are in the [knowledge base](../reference/logic_knowledge_base.md#oatl), and the
model format in [costCGS sections](../reference/file_formats.md#costcgs-sections).

## Model

Type `costCGS` ([format](../reference/file_formats.md#costcgs-sections)). A joint action
is one action per agent, written as a token such as `AA^` (agents 1, 2, 3 play
`A`, `A`, `^`); agents are numbered from 1. An entry of `Costs_for_actions` is
what the Demon, the player who erases joint actions, pays to erase joint action
`a` at state `s`; a cost vector is summed into one number.

A joint action may have no cost, as the self-loops of the example model below.
The check then fails with an error of type
`model`, naming the operator, the states and the model's joint actions that have
no cost, only when the result of
a modal subformula at some state depends on those costs: each fixpoint is run
with missing costs at +inf and at 0, and the two results must agree. A state's
only joint action needs no cost, since the Demon may never erase all actions of
a state.

A model written with `Transition_With_Costs` gives each edge a cost and no
joint actions. Only the coalition of all agents can be read on it (that is what
[OL](ol.md) uses); any other coalition is a `model` error, because
the agents' separate choices are not in the model.

## Formula language

Parser: `model_checker/parsers/formulas/OATL/parser.py`

```text
phi ::= p | true | false | !phi | phi && phi | phi || phi | phi -> phi
      | <A><n> X phi | <A><n> F phi | <A><n> G phi
      | <A><n> (phi U psi) | <A><n> (phi R psi) | <A><n> (phi W psi)
```

`<A><n>` needs a non-empty coalition `A` and a budget `n >= 0`. With `n = 0`
the Demon erases only zero-cost joint actions. `phi` and `psi` are state
formulas, and `theta` below stands for the path formula after the prefix, such
as `X phi`. Parentheses around a binary operator are optional.

## Semantic denotations

A Demon erases joint actions of the model, at a cost. `<A><n> theta` holds at a
state when the Demon, spending at most `n` per step and never erasing all
actions of a state, can erase actions so that whatever coalition `A` plays, some
remaining path satisfies `theta`. The budget applies to each step on its own,
not to the whole path. Agents outside `A` play in the Demon's favour, so
`<A><n> phi` does not imply the ATL formula `<A> phi`, and OATL does not use ATL
results as a shortcut.

Every subformula is evaluated bottom-up to the set of states where it holds, and
the formula holds in the model when the initial state is in the final set. One
step is the Demon pre-image `Pre_n(A, S)`, for a set of states `S`. An A-action
at a state is the coalition's part of a joint action (for `A = {1,2}`, the joint
action `AA^` gives the A-action `AA`); its successors are the states its joint
actions lead to. A state with no transition is never in `Pre_n(A, S)`; any
other state is in it when:

1. some A-action there has a successor in `S`, and
2. the joint actions of all A-actions whose successors miss `S` cost at most
   `n` in total.

The Demon must erase exactly the A-actions that miss `S`: one left in place
could be chosen by `A`, and then all its paths would leave `S`. Temporal
operators are fixpoints of `Pre_n`, where `T` ranges over sets of states and
`|`, `&` are union and intersection; least fixpoints iterate up from the
starting set, greatest ones down from it. Table 1 gives the fixpoint of each
operator:

**Table 1: OATL temporal operators as fixpoints of `Pre_n`.**

| Formula | Fixpoint |
| :--- | :--- |
| `<A><n> X phi` | `Pre_n(A, phi)` |
| `<A><n> phi U psi` | least `T = psi \| (phi & Pre_n(A, T))` |
| `<A><n> phi R psi` | greatest `T = psi & (phi \| Pre_n(A, T))` |
| `<A><n> F phi` | least `T = phi \| Pre_n(A, T)` |
| `<A><n> G phi` | greatest `T = phi & Pre_n(A, T)` |
| `<A><n> phi W psi` | greatest `T = (phi \| psi) & (psi \| Pre_n(A, T))` |

For example, on the attack model of the paper
([oatl_3agents_medium_6states_costs.txt](https://github.com/VITAMIN-organisation/vitamin-model-checker/blob/main/model_checker/tests/fixtures/costCGS/OATL/oatl_3agents_medium_6states_costs.txt)),
agents 1 and 2 are the attackers, the Demon blocks them, and
`<1,2><2> G !(r && s && g)` is false at `s0` and `<1,2><3> G !(r && s && g)`
is true: 3 is the least budget that blocks the attack, as the paper states.

`DemonicPreimage` groups the joint actions of each state by the coalition's
part once per check; see [algorithm design](index.md).

## Theory vs implementation

Table 2 sets the paper next to the code:

**Table 2: OATL theory and implementation.**

| Aspect | Paper (AAMAS 2024) | Code |
| :--- | :--- | :--- |
| Temporal operators | `X`, `U`, `R` (Def. 1) | Also `F`, `G`, `W`, computed directly; they give the same states as `true U phi`, `false R phi` and `psi R (phi \|\| psi)` |
| Cost | A partial function to positive integers, one number per joint action | A cost may be 0; a cost vector is summed into one number; a missing cost is an error only when a result depends on it, never silently 0 |
| Empty coalition | `A` is any subset of `Ag` (Def. 1) | `<>` is a syntax error |
| Edge-cost models | Not in the paper | `Transition_With_Costs`, coalition of all agents only (used by OL) |

## Code map

Table 3 lists the files of the checker; paths are relative to
`model_checker/algorithms/explicit/`.

**Table 3: OATL code map.**

| Path | Role |
| :--- | :--- |
| `OATL/OATL.py` | Entry, costCGS check |
| `OATL/solver.py` | Operator dispatch, builds `DemonicPreimage` |
| `OATL/operators.py` | X, F, G, U, R, W fixpoints and the missing-cost check |
| `OATL/preimage.py` | `DemonicPreimage`, the `Pre_n` computation |

## Tests

[test_correctness.py](https://github.com/VITAMIN-organisation/vitamin-model-checker/blob/main/model_checker/tests/integration/algorithms/oatl/test_correctness.py)
covers the budget threshold above, budget 0, the cost sum over A-actions,
agents outside `A`, `U` as least and `W` as greatest fixpoint, and the
missing-cost error.
