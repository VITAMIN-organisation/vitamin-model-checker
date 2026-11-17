# TOL algorithm

The TOL checker decides `{Jn} phi` on a `timedCGS` model with edge costs: as in
[OL](ol.md), a Demon (the player that disables edges at a cost, see
[OATL](oatl.md#demon-pre-image)) with a budget of `n` per step disables edges,
and the formula asks whether it can make every remaining path satisfy `phi`;
formulas may also carry clock guards and freezes as in [TCTL](tctl.md). Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#tol---timed-obstruction-logic),
the model file in [timedCGS sections](../reference/file_formats.md#timedcgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers)
on the regions of the [region graph](tctl.md#region-graph) of TCTL. Everything
except `{Jn}` is computed as in [TCTL](tctl.md#overview), including freezes;
`res` likewise lists only the locations of regions that time and edge steps
reach from the initial region ([TCTL result](tctl.md#result)). TOL has no `X` operator
([knowledge base](../reference/logic_knowledge_base.md#tol---timed-obstruction-logic)).

## Obstruction step

`Down(Z)`, the TOL [pre-image](index.md#overview) of a set of regions `Z`, keeps a
region `r` when all of these hold:

1. Time step: `r` itself and the time step from `r` to the next clock region stay
   in `Z`, because the Demon cannot disable a time step, and a delay of 0 is one.
2. Cost: an edge of `r`'s location leaves `Z` when it can be taken from `r` and
   leads to a region outside `Z`; the leaving edges cost at most the budget `n` in
   total, so the Demon can disable all of them.
3. Strict subset: the leaving edges are not all the edges of `r`'s location,
   counting edges that cannot be taken from `r` too, because the Demon removes a
   strict subset of a state's edges (Def. 6, p. 3).

The step of delay 0 follows AAMAS 2025 read literally: a path is "an infinite
sequence of consecutive delays and discrete transitions" (p. 3), with delays that
may be 0, and "every zone has a transitive $\epsilon$ delay transition to itself"
(p. 4), where an $\epsilon$ delay transition is the paper's time step between
zones. The same paragraph also says such a transition "is not reflexive between
zones", then "Since an $\epsilon$ transition is reflexive, the time successor
relation is also reflexive"; the checker takes the reflexive reading. It keeps
every region a step to itself, so no region is a dead end. It also makes
`Down(Z)` a subset of `Z`: a path may stay in its region forever, so `{Jn} F phi`
gives exactly `[[phi]]` (the regions where `phi` holds) and `{Jn} (phi U psi)`
exactly `[[psi]]`, on every model and for every budget `n`. `G`, `R` and `W` still
depend on `n`, because the cost and strict-subset conditions above can remove a
region of `Z` from `Down(Z)`. On `tol_cost_2states.txt`, `{J2} F p` holds only at
`s1`.

The paper is not consistent on this point. Its own algorithm gives the same `F`
and `U`: Algorithm 2 (p. 5) computes `{Jn} (phi U psi)` as a
[least fixpoint](index.md#overview) that starts from `[[psi]]` with no condition
on time, and Proposition 1 (p. 5) says the pre-image $\blacktriangledown(n, Z)$
(the checker's `Down(Z)`) holds a state iff the state is in `Z`. Theorem 2 (p. 6)
says instead that grade-0 TOL, translated as on p. 6, is TCTL, whose `A` ranges
only over paths along which time grows without bound
([Time-divergent paths](tctl.md#time-divergent-paths)). The two disagree on
`tol_cost_2states.txt` (see [Grade 0](#grade-0)). The paper does not mention such
paths and gives no pre-image restricted to them, so the checker follows its
Algorithm 2 and keeps the paths where time stands still. The original VITAMIN
repository has no TOL checker to compare.

An edge's cost comes from its cell in the `Transition_With_Costs` matrix:

- `0`: no edge.
- `*`: an edge of cost 0 to the cell's column (a self-loop on the diagonal).
- `a:b`: an edge of cost `a + b`, so `0:0` is an edge of cost 0.
- any other cell: an edge whose cost is that number.

### Example: the only edge

The test model `tol_only_edge.txt` in `model_checker/tests/fixtures/timedCGS/` has
`p` at `s0` and not at `s1`. The only edge of `s0`, of cost 1, leads to `s1`, which
has a self-loop; both have the invariant `x<=10` and no edge resets `x`.
`{J1}F (p : x>3)` fails at the initial state, `s0` with `x=0`: `F` needs every path
the Demon leaves to reach `p` with `x>3`, and the Demon must keep the only edge, so
a path can leave `s0` at `x=1` and never meet `p` again. In the region of `s0` with
`x>3` the formula holds at once, so `res` still lists `s0`.

## Grade 0

The grade is the `n` in `{Jn}`, the Demon's budget per step (the paper calls it the
grade of the strategic operator). AAMAS 2025 allows `n = 0` (Def. 10, p. 4) and
edges of cost 0 (Def. 4, `W : T -> N>=0`, p. 3, where N>=0 is the non-negative
integers), so `{J0} phi` is valid. The Demon never disables every edge of a state:
it removes a strict subset of the state's outgoing edges (Def. 6, p. 3). With
`n = 0` it can still remove edges of cost 0, including `*` cells.

Theorem 2 (p. 6) states that the fragment of TOL whose grades are all 0 is TCTL.
That holds only when the model has no edge of cost 0; the paper does not mention
this case, and the checker follows Def. 6 and the semantics of Def. 11 (p. 4).

Example: the test model `tol_zero_cost_edge.txt` in
`model_checker/tests/fixtures/timedCGS/`. In `s0`, an edge of cost 0 (`0:0`) leads
to `s1`, where `p` holds, and a self-loop of cost 5 stays in `s0`. `{J0} G !p` holds
at `s0`, because the Demon disables the edge to `s1` for free. TCTL `AG !p`, "on all
paths always `!p`", holds nowhere. When no edge costs 0, a grade-0 Demon can remove
nothing; on such a model the tests check that `{J0} F p` and `{J0} G !p` give the
same states as TCTL `AF p` and `AG !p` (`tol_positive_cost_branch.txt`). That does
not hold on every model without edges of cost 0, because of the step of delay 0
(see [Obstruction step](#obstruction-step)): on `tol_cost_2states.txt`, `{J0} F p`
gives `{s1}` and TCTL `AF p` gives `{s0, s1}`.

## Operators

`[[phi]]` is the set of regions where `phi` holds. Fixpoints, `R` and `W` are
defined in the [overview](index.md#overview).

**Table 1: TOL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `{Jn} F phi` | least fixpoint of `Z = [[phi]] \| Down(Z)` | `[[phi]]` |
| `{Jn} G phi` | greatest fixpoint of `Z = [[phi]] & Down(Z)` | all regions |
| `{Jn} (phi U psi)` | least fixpoint of `Z = [[psi]] \| ([[phi]] & Down(Z))` | `[[psi]]` |
| `{Jn} (phi R psi)` | greatest fixpoint of `Z = [[psi]] & ([[phi]] \| Down(Z))` | all regions |
| `{Jn} (phi W psi)` | greatest fixpoint of `Z = ([[phi]] \| [[psi]]) & ([[psi]] \| Down(Z))` | all regions |
