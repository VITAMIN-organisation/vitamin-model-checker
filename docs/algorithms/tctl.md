# TCTL algorithm

The TCTL checker decides CTL formulas with clock constraints, such as
`AF (p : x<=3)`, on a `timedCGS` model: locations with real-valued clocks,
invariants on locations and guards and resets on edges. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#tctl---timed-ctl), the model
file in [timedCGS sections](../reference/file_formats.md#timedcgs-sections).

## Zone graph

Clock values are real numbers, so the checker groups them into zones (sets of
clock values described by bounds on clocks and clock differences) and works on
regions, pairs (location, zone):

1. Clocks named in the formula, by a freeze `x . phi` or a guard such as
   `phi : x<=3`, are added to the model's clocks if new.
2. The initial region is the initial location with every clock at 0, cut by the
   location's invariant. If that is empty, the graph is empty.
3. From each region, the graph is built breadth first with two kinds of successor:
   letting time pass (every clock grows, then the invariant applies) and taking an
   edge (the guard applies, then the resets, then the target's invariant). Empty
   zones and time steps that lead back to the same region are dropped.
4. Each zone is normalized against the largest constant each clock is compared
   with in the model and the formula, so the graph is finite.
5. Each new zone is then split on the formula's clock bounds, the comparisons of a
   clock with a constant in the formula (`x<=3` in `AG (p : x<=3)`). For each bound,
   the zone is cut into the part that meets it and the part that fails it, and each
   non-empty part is a region of its own. A time step from a part reaches every
   later part. Example: at a location with invariant `x<=10`, the time successor
   of the initial region `x=0` is cut into `0<=x<=3` and `3<x<=10`. Regions may
   overlap, as `x=0` and `0<=x<=3` do.

The split is how the checker builds the zone graph ZG(A, phi) of AAMAS 2025
Algorithm 1 (p. 5), whose labels hold a clock constraint of the formula only where
the clock values meet it. For each bound, either every clock value in a region
meets it or every value fails it, so a constraint is true or false for the whole
region.

## Overview

Each subformula becomes a set of regions: an atom is every region whose location
has it, and `!`, `&&`, `||`, `->` are set operations over all regions. A clock
constraint such as `x<=3` is the set of regions whose zone meets it, and
`phi : x<=3` is `phi && x<=3`: both must hold in the same region, because a clock
constraint is a formula of its own in the grammar of AAMAS 2025 (Def. 10, p. 4).

A freeze `j . phi` is evaluated as `phi`, as in AAMAS 2025 Algorithm 1 (line 19,
p. 5). Here `j` is a formula clock: a clock that only the formula names, added to
the model in step 1, which starts at 0 and is never reset by an edge. The result
is right where `j` is still 0, such as a freeze at the start of the formula. Under
a temporal operator it can be wrong. Example: the test model
`tctl_tol_invariant10.txt` in `model_checker/tests/fixtures/timedCGS/` has one
location `s0` with a self-loop and invariant `x<=10`. `EF (x>8 && j . EF (j>=2))`
should be false, because after `x>8` time cannot advance by 2, but the checker
gives true. TOL freezes behave the same way.

`Pre(Z)`, the [pre-image](index.md#overview), is the set of regions with a time
step or an edge of the zone graph into `Z`. There is no `X` operator: the next
region in dense time is not unique.

## Operators

`All` is the set of all regions and `[[phi]]` the set of regions where `phi`
holds. Fixpoints are defined in the [overview](index.md#overview).

**Table 1: TCTL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `EF phi` | least fixpoint of `Z = Z \| Pre(Z)` | `[[phi]]` |
| `EG phi` | greatest fixpoint of `Z = [[phi]] & Pre(Z)` | `All` |
| `AF phi` | `All` minus the greatest fixpoint of `Z = (All - [[phi]]) & Pre(Z)` | `All` |
| `AG phi` | `All` minus the least fixpoint of `Z = Z \| Pre(Z)` | `All - [[phi]]` |
| `E(phi U psi)` | least fixpoint of `Z = [[psi]] \| ([[phi]] & Pre(Z))` | `[[psi]]` |
| `A(phi U psi)` | `All` minus the least fixpoint of `Z = N \| ((All - [[phi]]) & N & (All - Pre(All - Z)))`, with `N = All - [[psi]]` | `N` |

Because the `A(phi U psi)` iteration starts from every region where `psi` fails,
its result holds only where `psi` holds. Example: one clock `x`; `s0` goes to
`s1`, which loops; only `s1` is labelled `p`; both locations have the invariant
`x<=2`. `AF p` holds at `s0`, but `A(true U p)` does not.

## Result

The formula holds when the initial region is in the final set. `res` lists the
locations of the regions in the set, so a location the zone graph never reaches is
never listed, and `initial_state` gives the verdict, as in the
[shared steps](index.md#steps-shared-by-the-set-based-checkers).
