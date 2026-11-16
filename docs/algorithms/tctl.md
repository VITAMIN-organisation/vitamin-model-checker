# TCTL algorithm

The TCTL checker decides CTL formulas with clock constraints, such as
`AF (p : x<=3)`, on a `timedCGS` model: locations with real-valued clocks,
invariants on locations and guards and resets on edges. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#tctl---timed-ctl), the model
file in [timedCGS sections](../reference/file_formats.md#timedcgs-sections).

## Region graph

Clock values are real numbers, so the checker groups them into clock regions and
works on the region graph of IC 1993 (Alur, Courcoubetis and Dill, p. 20). A
clock's largest constant is the largest number the model or the formula compares
it with. A clock region is a set of clock values that agree on each clock's
integer part, up to that clock's largest constant, and on the order of the
fractional parts of the clocks that are at most their largest constant (IC 1993,
p. 16). A region is a pair (location, clock region); two regions never overlap.
Clock values in one region satisfy the same formulas whose constants are at most
the largest constants (IC 1993, Lemma "Equivalence of Clock Assignments",
pp. 16-17), so the checker labels a region as a whole. The graph is built as
follows:

1. Clocks named in the formula, by a freeze `j.phi` (which sets the formula
   clock `j` to 0 and then checks `phi`, see the [overview](#overview)) or a
   guard such as `phi : x<=3`, are added to the model's clocks if new. A freeze
   on a clock declared in the model's `Clocks` section is a
   [`semantic`](../reference/logic_knowledge_base.md#operators-and-names) error
   that names the clock: AAMAS 2025 (Def. 10, p. 4) requires the model's clocks
   and the formula's clocks to be disjoint sets.
2. Each clock's largest constant is computed; the formula `AG (p : x<=3)`
   contributes 3 for `x`.
3. The initial region is the initial location with every clock at 0, restricted to
   the location's invariant. If that leaves no clock values, the graph is empty.
4. From each region, the graph is built breadth first with two kinds of successor
   and one link, computed as in step 5:
   - letting time pass leads only to the next clock region, the first one time
     reaches after leaving the current one, if the invariant allows it. A region
     that time cannot leave within the invariant, such as `x=10` under `x<=10` or
     one with every clock above its largest constant, has no time step: a step
     back to itself would add nothing.
   - taking an edge: the guard applies, then the resets, then the target's
     invariant; each clock region of the result is a successor.
   - for each clock `j` that a freeze `j.phi` in the formula names, setting `j`
     to 0 gives one clock region, which joins the graph, is expanded like any
     other region, and is recorded as the current region's freeze reset. The
     link is not a step: time and edges never follow it.
5. The checker computes successors as zones (sets of clock values described by
   bounds on clocks and clock differences), normalizes each zone against the
   largest constants so the graph is finite, and cuts it into clock regions. Each
   clock `x` is compared with every integer from 0 to its largest constant `c_x`.
   Where both `x` and `y` are at most their largest constants, `x - y` is compared
   with every integer from `-c_y` to `c_x`.

Example: the test model `tctl_tol_invariant10.txt` in
`model_checker/tests/fixtures/timedCGS/` has one clock `x` and one location `s0`
with a self-loop that does not reset `x`, and the invariant `x<=10`. Time there
runs through 21 clock regions: `x=0`, `0<x<1`, `x=1`, and so on up to `9<x<10`
and `x=10`. `E (x<=3 U x>=5)` is false, because time passes through `3<x<5`, where
neither side holds. A time step straight from `x<=3` to `x>=5` would skip those
regions, and the checker gave true before it built regions.

The nodes of this graph are finer than those of the zone graph of AAMAS 2025,
Algorithm 1 (p. 5), whose labels are on zones. A zone can hold clock values with
different futures: under the invariant `x<=10`, `x=2` can still reach `x=4`, while
`x=9` only reaches values up to 10 and never `x=4`. A label on such a zone would
hold for some of its values only.

The graph grows with the largest constants and, faster, with the number of
clocks. The test models in `model_checker/tests/fixtures/timedCGS/` have one clock
with constants up to 10 and 4 to 42 regions. One location with clocks `x` and `y`,
invariants `x<=12` and `y<=12` and a self-loop with guard `x>=1` that resets `y`
gives 422 regions.

## Overview

Each subformula becomes a set of regions: an atom is every region whose location
has it, and `!`, `&&`, `||`, `->` are set operations over all regions. A clock
constraint such as `x<=3` is the set of regions where every clock value meets it, and
`phi : x<=3` is `phi && x<=3`: both must hold in the same region, because a clock
constraint is a formula of its own in the grammar of AAMAS 2025 (Def. 10, p. 4).

A freeze `j.phi` holds in a region when `phi` holds in the region's freeze
reset, the region reached by setting `j` to 0 there (step 4). This is the
semantics of AAMAS 2025 (Def. 11, p. 4: `j.phi` holds at `(l, v)` when `phi`
holds at `(l, v[j <- 0])`) and the region labelling of IC 1993 (p. 22), which
checks an until along the paths that start at the region with the formula clock
reset "instead of v itself". Here `j` is a formula clock: a clock that only the
formula names, added to the model in step 1; it starts at 0 with the model's
clocks, no edge resets it, and only a freeze does. AAMAS 2025 Algorithm 1
(line 19, p. 5) instead computes `j.phi` as `phi`, which contradicts Def. 11 of
the same paper. Example: on `tctl_tol_invariant10.txt`, with the invariant
`x<=10`, `EF (x>8 && j.EF (j>=2))` is false, because after `x>8` time cannot
advance by 2, and `EF (x>=5 && j.AG (j<=4))` is true, because at `x=6`, `j` runs
to 4 and time stops. TOL freezes work the same way.

`Pre(Z)`, the [pre-image](index.md#overview), is the set of regions with a time
step or an edge of the region graph into `Z`. There is no `X` operator: the next
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
locations of the regions in the set that time and edge steps reach from the
initial region, so a location that no time or edge step reaches, or a region
that only a freeze reset leads to, is never listed; `initial_state` gives the
verdict, as in the
[shared steps](index.md#steps-shared-by-the-set-based-checkers).
