# TOL algorithm

The TOL checker decides `{Jn} phi` on a `timedCGS` model with edge costs: as in
[OL](ol.md), a Demon (the player that disables edges at a cost, see
[OATL](oatl.md#demon-pre-image)) with a budget of `n` per step disables edges, and the formula
asks whether it can make every remaining path satisfy `phi`; formulas may also
carry clock guards and freezes as in [TCTL](tctl.md). Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#tol---timed-obstruction-logic),
the model file in [timedCGS sections](../reference/file_formats.md#timedcgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers)
on locations, not on regions. It builds the [zone graph](tctl.md#zone-graph) of
TCTL, with the formula's clocks added, but uses it only for clock guards
(`phi : x<=3` and steps under a guard) and for freezes; the result of each of
these is turned back into locations.

## Obstruction step

`Down(Z)`, for a set of locations `Z`, keeps a location `s` when:

1. `s` has an edge into `Z`; under a clock guard, `s` must instead have a region
   with an edge of the zone graph into a region of `Z` whose zone satisfies the
   guard;
2. the edges from `s` to locations outside `Z` cost at most `n` in total, so the
   Demon can disable all of them.

An edge's cost is its matrix cell: `0` and `*` cost 0, a cell such as `1:2` costs
the sum of its parts, and any other cell is read as a number. The guard used is the
first one found in the operand (the right operand for `U` and `R`, the left for
`W`).

## Operators

`[[phi]]` is the set of locations where `phi` holds.

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
