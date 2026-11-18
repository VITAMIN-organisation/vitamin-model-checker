# RBATL algorithm

The RBATL checker decides `<A><b> phi`: can coalition `A` force `phi` while the
summed cost of its moves along the path stays within the bound vector `b`? It runs
on a `costCGS` model, where each joint action has a cost vector in each state, one
value per resource.
Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl), the model file
in [costCGS sections](../reference/file_formats.md#costcgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers):
it computes the set of states where each subformula holds and checks the initial
state. A coalition operator is computed from the bounded
[pre-image](index.md#overview) (next section), once for `X` and, for `F`, `G` and
`U`, as one [fixpoint](index.md#overview) for each part of the bound still
unspent (see [operators](#operators)).

## Bounded pre-image

`Pre(Z, c)`, for a cost vector `c`, is the [pre-image](index.md#overview) of `Z`
restricted to steps that cost at most `c`. A state `s` is in `Pre(Z, c)` when the coalition
has a move `m` (one action per member) such that every joint action that contains
`m`, whatever the other agents play:

1. leads into `Z`;
2. costs at most `c` at `s`: `cost_i <= c_i` for each resource `i` that `c` covers
   (with `c` of length 1, the second cost value is not limited). RBATL asks this of
   one joint action of the move that has a cost in the model, and RABATL of every
   joint action of the move (see below).
   A bound longer than the model's cost vectors is a validation error; a shorter
   one is accepted (see [Differences from the papers](#differences-from-the-papers)).

In RB-ATL the cost of a move is the sum of the costs of the members' own actions
only (Catta et al., PRIMA 2024, p. 5), and the RB-ATL Pre leaves out the loop over
the other agents' actions that RAB-ATL needs (p. 9). A `costCGS` model gives the
cost of whole joint actions, so the checker cannot read the members' share off it.
A joint action within the bound is that share when the other agents' actions are
free, as the idle action is in the paper's example; when an opponent's action has a
cost, RBATL ignores the opponent that picks it. RABATL, whose costs are split per
agent (`Costs_for_actions_split`), sums the members' shares and needs every joint
action within the bound, as `Pre(C, X, b)` on p. 9 does. The original code (`RBATL.py:80-86`)
asked for one joint action within the bound; the paper does not follow it either.
Two consequences follow:

- A joint action with no cost for `s` in the model is not counted in RBATL, and in
  RABATL a move that contains one is never in `Pre(Z, c)`.
- With `c_i = 0` only moves of cost 0 in resource `i` stay, so `<1><0> F p` asks
  whether `p` can be forced with moves of cost 0 alone.

## Operators

The bound `b` limits the sum of the costs of the coalition's moves along every
path, for each resource: a strategy must keep every prefix of the path within `b`
(Catta et al., RAB-ATL, PRIMA 2024, Def. 4, p. 5). The cost of a move is the cost
defined in [Bounded pre-image](#bounded-pre-image); RABATL sums the members' costs
instead. A goal two steps of cost 1 away needs `b >= 2`.

The checker computes `W(b')`, the set of states where the formula holds when the
unspent part of the bound is `b'`, for every `b' <= b` (componentwise), smallest
first, so every `b'' < b'` (componentwise `<=` and not equal) is done before
`b'`. A state is in `W(b')` when the coalition can make a move that costs at most
`b' - b''` into `W(b'')` for some `b'' < b'`, or a move of cost 0 that the
fixpoint below iterates. This is the loop over smaller budgets of Algorithm 2
(PRIMA 2024, p. 12). Table 1 lists `W(b')`; `[[phi]]` is the set of states where
`phi` holds and `paid(b')` is the union of `Pre(W(b''), b' - b'')` over all
`b'' < b'`. When two budgets `b''' < b''` give the same set, `paid` uses only
`b'''`: it leaves more for the paid move, so the result does not change.

**Table 1: RBATL operators for one budget `b'`.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<A><b> X phi` | `Pre([[phi]], b)` | (no iteration) |
| `<A><b> F phi` | least fixpoint of `Z = Z \| Pre(Z, 0) \| paid(b')` | `[[phi]]` |
| `<A><b> G phi` | greatest fixpoint of `Z = (Pre(Z, 0) \| paid(b')) & [[phi]]` | all states |
| `<A><b> (phi U psi)` | least fixpoint of `Z = Z \| ((Pre(Z, 0) \| paid(b')) & [[phi]])` | `[[psi]]` |

Example: one agent; in `s0` action `A` (cost 1) leads to `s1`, in `s1` action `A`
(cost 1) leads to `s2`, where `p` holds; action `B` (cost 0) loops in `s0` and
`s1`, and `s2` loops at cost 0. `<1><1> F p` gives `{s1, s2}`: from `s0` the two
steps cost 2. `<1><2> F p` gives `{s0, s1, s2}`. `<1><1> G !p` gives
`{s0, s1}`, since `B` keeps the agent in place at cost 0.

The number of budgets is the product of `b_i + 1` over the bound's entries, and
the time grows with it. Measured with `<1,2><b,b> F p` on
`model_checker/tests/fixtures/costCGS/RBATL/rbatl_2agents_8states_sensor.txt`:
`(20,20)` takes 0.02 s, `(100,100)` 0.5 s and `(300,300)` 5.9 s (best of 3 runs of
`model_checking`). A bound that needs
more than 100000 budgets is a validation error that names it.

[RABATL](rabatl.md) runs the same algorithm; only the cost of a joint action is
computed differently.

## Differences from the papers

Two points differ from the text of Algorithm 2 and follow Def. 5 (p. 6), which
puts no condition on `phi` at the position where `psi` holds:

- Until with `b > 0`: line 34 intersects every paid move with `[[phi]]`, so a state
  where `psi` holds and `phi` does not never enters. The checker starts from
  `[[psi]]`.
- `G` with `b > 0`: lines 20-24 build the set as a least fixpoint seeded with the
  paid moves into the sets of smaller budgets (for `b' = 0`, the cost-0 `G` set of
  lines 13-18). The checker computes the greatest fixpoint of the same update,
  which is the set of Def. 5 and can be larger on a concurrent model. Example
  with coalition `{1}` and `q` everywhere: `s` goes to `s` under `AY` and `BX` and
  to `t` under `AX` and `BY` at cost 0, `t` goes to `u` under `CX` at cost 1, and
  `u` loops at cost 0. `<1><1>G q` holds at `s`: playing `A` at `s` and `C` at `t`
  keeps every path within cost 1. Algorithm 2 seeds its least fixpoint with the
  paid move into `{u}` and stops at `{t, u}`, because from `s` agent 2 can answer
  `A` by staying in `s`, which is not yet in the set. The fixture
  `rbatl_2agents_3states_loop.txt` is this model.

The cost of an Until counts the moves until `psi` holds, as in Algorithm 2.

A bound may have fewer values than the model has resources. The checker then
limits only the resources that the bound covers and leaves the others unlimited.
This is a VITAMIN convention. PRIMA 2024 takes a bound from `N^r`, the vectors of
`r` natural numbers where `r` is the number of resources (p. 8: "a bound b will be
any element of N^r"). RABATL follows the same convention.

PRIMA 2024 gives every agent the idle action at cost 0 in every state (p. 4) and
leaves the self-loops of the joint action (idle, idle) out of Fig. 1 (p. 5). The
checker adds no move that a `Transition` row does not list, so the sensor fixture
`rbatl_2agents_8states_sensor.txt` writes them: `II` (idle is `I`) at cost 0 in
every state. It also has `CC` from `s7` to `s6`, the figure's (send1b, send2b), at
cost `4:0`. With the loops, `<1,2><0,0>G !p` holds at `s0`: both agents stay idle.

WOA 2024 (Table 1) reports its rover mission formula true with bound `(5,1)` and
false with `(2,2)`. The test `test_rover_mission_formula_runs` writes the formula as
`<1,2><5,1>F(oc && rm && <1><0,0>F((pl || pr) && <1><0,0>F(oc && rm)))` on
`rbatl_2agents_11states_rover.txt` (the paper writes the coalition without bounds).
The checker gives false at `s0` for `(5,1)` and `(2,2)` and true for `(5,3)`. Every
move into `s4` costs `(2,4)`, `(3,5)` or `(5,3)`: comparing each resource rejects
all three for `(5,1)`, while comparing vectors in lexicographic order (first
resource first) accepts them, which the original VITAMIN code (commit e8ea8773)
did.
