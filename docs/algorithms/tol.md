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
on locations, not on regions. It builds the [zone graph](tctl.md#zone-graph) of
TCTL, with the formula's clocks added, but uses it only for clock guards
(`phi : x<=3` and steps under a guard) and for freezes; the result of each of
these is turned back into locations.

## Obstruction step

`Down(Z)`, the TOL [pre-image](index.md#overview) of a set of locations `Z`, keeps
a location `s` when:

1. `s` has an edge into `Z`; under a clock guard, `s` must instead have a region
   with an edge of the zone graph into a region of `Z` whose zone satisfies the
   guard;
2. the edges from `s` to locations outside `Z` cost at most `n` in total, so the
   Demon can disable all of them.

An edge's cost comes from its cell in the `Transition_With_Costs` matrix:

- `0`: no edge.
- `*`: a self-loop of cost 0 on the row's state, whatever the column.
- `a:b`: an edge of cost `a + b`, so `0:0` is an edge of cost 0.
- any other cell: an edge whose cost is that number.

The guard used is the first one found in the operand (the right operand for `U`
and `R`, the left for `W`).

## Grade 0

The grade is the `n` in `{Jn}`, the Demon's budget per step (the paper calls it the
grade of the strategic operator). AAMAS 2025 allows `n = 0` (Def. 10, p. 4) and
edges of cost 0 (Def. 4, `W : T -> N>=0`, p. 3, where N>=0 is the non-negative
integers), so `{J0} phi` is valid. The Demon never disables every edge of a state:
it removes a strict subset of the state's outgoing edges (Def. 6, p. 3). With
`n = 0` it can still remove edges of cost 0, including `*` self-loops.

Theorem 2 (p. 6) states that the fragment of TOL whose grades are all 0 is TCTL.
That holds only when the model has no edge of cost 0; the paper does not mention
this case, and the checker follows Def. 6 and the semantics of Def. 11 (p. 4).

Example: the test model `tol_zero_cost_edge.txt` in
`model_checker/tests/fixtures/timedCGS/`. In `s0`, an edge of cost 0 (`0:0`) leads
to `s1`, where `p` holds, and a self-loop of cost 5 stays in `s0`. `{J0} G !p` holds
at `s0`, because the Demon disables the edge to `s1` for free. TCTL `AG !p`, "on all
paths always `!p`", holds nowhere. When no edge costs 0, a grade-0 Demon can remove
nothing; on such a model the tests check that `{J0} F p` and `{J0} G !p` give the
same states as TCTL `AF p` and `AG !p`.

## Operators

`[[phi]]` is the set of locations where `phi` holds. Fixpoints, `R` and `W` are
defined in the [overview](index.md#overview).

**Table 1: TOL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `{Jn} X phi` | `Down([[phi]])` | (no iteration) |
| `{Jn} F phi` | least fixpoint of `Z = [[phi]] \| Down(Z)` | `[[phi]]` |
| `{Jn} G phi` | greatest fixpoint of `Z = [[phi]] & Down(Z)` | all locations |
| `{Jn} (phi U psi)` | least fixpoint of `Z = [[psi]] \| ([[phi]] & Down(Z))` | `[[psi]]` |
| `{Jn} (phi R psi)` | greatest fixpoint of `Z = [[psi]] & ([[phi]] \| Down(Z))` | all locations |
| `{Jn} (phi W psi)` | greatest fixpoint of `Z = ([[phi]] \| [[psi]]) & ([[psi]] \| Down(Z))` | all locations |

A freeze `x . phi` maps the locations of `phi` to regions, resets `x` in every
region, and keeps the locations whose reset region matches.
