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

1. Clocks named in the formula, by a freeze `x . phi` or a guard, are added to the
   model's clocks if new.
2. The initial region is the initial location with every clock at 0, cut by the
   location's invariant. If that is empty, the graph is empty.
3. From each region, the graph is built breadth first with two kinds of successor:
   letting time pass (every clock grows, then the invariant applies) and taking an
   edge (the guard applies, then the resets, then the target's invariant). Empty
   zones and time steps that change nothing are dropped.
4. Each zone is normalized against the largest constant each clock is compared
   with in the model and the formula, so the graph is finite.

## Overview

Each subformula becomes a set of regions: an atom is every region whose location
has it, and `!`, `&&`, `||`, `->` are set operations over all regions. `phi : x<=3`
keeps the regions of `phi` whose zone can satisfy the guard. A freeze `x . phi`
keeps the regions that, with `x` reset to 0, satisfy `phi`.

`Pre(Z)` is the set of regions with an edge of the zone graph into `Z`, kept only
when its zone, under the guard of the operand (if any), is not empty. There is no
`X` operator: the next region in dense time is not unique.

## Operators

`All` is the set of all regions and `[[phi]]` the set of regions where `phi`
holds.

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
locations of the regions in the set, and `initial_state` gives the verdict, as in
the [shared steps](index.md#steps-shared-by-the-set-based-checkers).
