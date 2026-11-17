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
   contributes 3 for `x`. TCTL also adds the tick clock, with largest constant 1,
   which marks each time unit that passes so that the checker can keep the
   time-divergent paths, those along which time grows without bound (see
   [Time-divergent paths](#time-divergent-paths)). No formula or model can name
   it, and TOL does not add it.
3. The initial region is the initial location with every clock at 0, restricted to
   the location's invariant. If that leaves no clock values, the graph is empty.
4. From each region, the graph is built breadth first with two kinds of successor
   and one link, computed as in step 5 (a tick region, one where the tick clock
   has reached 1, instead has a single successor: the same region with the tick
   clock set to 0, a step that takes no time):
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

Example: the test model `tctl_invariant10_exit.txt` in
`model_checker/tests/fixtures/timedCGS/` has one clock `x`. Location `s0`, where `p`
holds, has a self-loop that does not reset `x`, the invariant `x<=10` and an edge
with guard `x>=10` to `s1`, which has no invariant. At `s0`, `x` runs through 21
clock regions of its own (the tick clock splits some of them further): `x=0`, `0<x<1`, `x=1`, and so on up to `9<x<10` and `x=10`.
`E (x<=3 U x>=5)` is false, because time passes through `3<x<5`, where
neither side holds. A time step straight from `x<=3` to `x>=5` would skip those
regions, and the checker gave true before it built regions.

The nodes of this graph are finer than those of the zone graph of AAMAS 2025,
Algorithm 1 (p. 5), whose labels are on zones. A zone can hold clock values with
different futures: under the invariant `x<=10`, `x=2` can still reach `x=4`, while
`x=9` only reaches values up to 10 and never `x=4`. A label on such a zone would
hold for some of its values only.

The graph grows with the largest constants and, faster, with the number of
clocks. The test models in `model_checker/tests/fixtures/timedCGS/` have one clock
with constants up to 10 and 4 to 42 regions without the tick clock (the graph TOL
uses), 7 to 62 with it. One location with clocks `x` and `y`, invariants `x<=12`
and `y<=12` and a self-loop with guard `x>=1` that resets `y` gives 422 regions
without the tick clock.

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
the same paper. Example: on `tctl_invariant10_exit.txt`, where `p` holds only at
`s0` and `s0` is left at `x=10`, `EF (x>8 && j.EF (p && j>=2))` is false, because
after `x>8` time advances by less than 2 before `s0` is left, and
`EF (x>=5 && j.AG (p -> j<=4))` is true, because from `x=6`, `j` reaches 4 when
`s0` is left. TOL freezes work the same way.

`Pre(Z)`, the [pre-image](index.md#overview), is the set of regions with a time
step, an edge or a tick reset of the region graph into `Z`. There is no `X`
operator: the next region in dense time is not unique.

## Time-divergent paths

`A` and `E` range over the time-divergent paths only. Baier and Katoen
(Principles of Model Checking, Def. 9.30, p. 701) define `E phi` to hold at `s`
when some path in `Paths_div(s)` satisfies `phi`, and `A phi` when every path in
it does, where `Paths_div(s)` is the set of time-divergent paths from `s`; on
p. 700 they add that "time-convergent paths are not of any importance for the
satisfaction of TCTL state formulae". Two kinds of path drop out:

- infinitely many edges in bounded time: on `tctl_zeno_cycle.txt`, `s0` has the
  invariant `x<=5` and a self-loop with guard `x>=1` that never resets `x`.
  Looping there forever keeps `x<=5`, so total time stays below 5, and `EG p` is
  false.
- paths where time stops: on `tctl_tol_minimal.txt`, time at `s0` stops at `x=2`
  and no edge resets `x`. A region with no time-divergent path is a timelock;
  there every `A` formula holds and every `E` formula fails, so `AF false` holds
  at `s0` and `EF p` does not. Baier and Katoen (p. 705) call `AG EG true` "a
  tautology in TCTL" for this reason.

A region records no elapsed time, so the checker counts time units with the tick
clock of [step 2](#region-graph). It starts at 0 and is set back to 0 each time
it reaches 1. Reaching 1 again takes a full time unit, so a path that passes tick
regions infinitely often is time-divergent; and along a time-divergent path the
tick clock reaches 1 again and again. A path is therefore time-divergent exactly
when it passes tick regions infinitely often. The tick reset itself takes no time
and changes no label, so it changes no formula's value (TCTL has no `X`).

Alur's thesis (Techniques for Automatic Verification of Real-Time Systems,
Stanford, 1991, Def. 5.26) tests a region path instead: each clock is infinitely
often 0 or above its largest constant. In this checker two edges may fire at the
same instant, so a self-loop that resets `x` at `x=0` would pass that test while
time stands still. The original VITAMIN repository has no TCTL checker to compare.

`E0(phi U psi)`, the regions with a path through `phi` into `psi`, is the least
fixpoint of `Z = [[psi]] | ([[phi]] & Pre(Z))`, starting from `[[psi]]`.
`EG_d phi`, the regions with a time-divergent path that stays in `phi`, is the
greatest fixpoint of `Z = [[phi]] & Pre(E0(phi U (Z & Tick)))`, with `Tick` the
set of tick regions: from a region of `Z`, a path stays in `phi` up to the next
tick region, which is again in `Z`. `EG_d true` is the set of regions with no
timelock.

## Operators

`All` is the set of all regions and `[[phi]]` the set of regions where `phi`
holds. Fixpoints are defined in the [overview](index.md#overview). Table 1
builds every operator from `E0` and `EG_d`:

**Table 1: TCTL operators.**

| Formula | Set computed |
| :--- | :--- |
| `E(phi U psi)` | `E0(phi U ([[psi]] & EG_d true))` |
| `EF phi` | `E(true U phi)` |
| `EG phi` | `EG_d phi` |
| `AF phi` | `All - EG_d (All - [[phi]])` |
| `AG phi` | `All - EF (All - [[phi]])` |
| `A(phi U psi)` | `All - (E((All - [[psi]]) U (All - [[phi]] - [[psi]])) \| EG_d (All - [[psi]]))` |

`A(phi U psi)` fails in two cases, the two parts of its row: some time-divergent
path reaches a region with neither `phi` nor `psi` before `psi`, or one never
reaches `psi`. Example:
`tctl_divergent_paths.txt` has `s0` with the invariant `x<=1`, a self-loop that
does not reset `x` and edges to `s1` (`p`) and `s2` (`q`), which have no invariant.
Every time-divergent path leaves `s0`, so `A(true U (p || q))` holds at `s0`, and
`A((!p) U p)` fails there through the path to `s2`.

## Result

The formula holds when the initial region is in the final set. `res` lists the
locations of the regions in the set that time and edge steps reach from the
initial region, so a location that no time or edge step reaches, or a region
that only a freeze reset leads to, is never listed; `initial_state` gives the
verdict, as in the
[shared steps](index.md#steps-shared-by-the-set-based-checkers).
