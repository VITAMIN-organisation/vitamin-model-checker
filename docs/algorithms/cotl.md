# COTL algorithm

The COTL checker decides `<L><n> phi` on an `ObstructionModel`: a graph of states
whose edges demons can disable. `L` is a legion, a set of demons (it may be empty,
`<>`), with a budget `n` per step; the formula asks whether the legion can play so
that, whatever the other demons do, every resulting path satisfies `phi`. Formula
syntax is in the [knowledge base](../reference/logic_knowledge_base.md#cotl), the
model file in
[ObstructionModel sections](../reference/file_formats.md#obstructionmodel-sections-cotl).

## Model

- Each demon has the actions its `Demon_actions` lines declare for a state, each
  with a cost of at least 1, plus the idle action `*`, which costs 0 and is always
  available.
- A curse is a joint action of all demons in a state. The `Curses` section lists
  the edges each curse disables; a curse it does not list disables nothing.
- A path may be finite: it stops when every edge out of its last state is disabled.

## One step

At a state `s`, the legion picks one action per member; the cost is the sum of
their costs. Every curse that agrees with that pick on the legion's demons is a
possible outcome, and leaves the edges of `s` it does not disable. A legion pick
that no listed curse extends leaves every edge; among such picks only the cheapest
is considered.

Two one-step sets are computed for a set of states `S`. A state `s` is in them
when the legion has a pick of cost at most `n` such that, for every outcome, the
remaining successors:

- `Next(S)`: are all in `S`, and there is at least one;
- `NextOrStop(S)`: are all in `S`, or there are none (the path stops).

## Operators

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers);
`[[phi]]` is the set of states where `phi` holds.

**Table 1: COTL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<L><n> X phi` | `Next([[phi]])` | (no iteration) |
| `<L><n> WX phi` | `NextOrStop([[phi]])` (weak next) | (no iteration) |
| `<L><n> F phi` | least fixpoint of `Z = [[phi]] \| Next(Z)` | `[[phi]]` |
| `<L><n> G phi` | greatest fixpoint of `Z = [[phi]] & NextOrStop(Z)` | `[[phi]]` |
| `<L><n> (phi U psi)` | least fixpoint of `Z = [[psi]] \| ([[phi]] & Next(Z))` | `[[psi]]` |
| `<L><n> (phi R psi)` | greatest fixpoint of `Z = [[psi]] & ([[phi]] \| NextOrStop(Z))` | `[[psi]]` |
| `<L><n> (phi W psi)` | greatest fixpoint of `Z = ([[phi]] \| [[psi]]) & ([[psi]] \| NextOrStop(Z))` | `[[phi]] \| [[psi]]` |

`X`, `F` and `U` need the path to go on; `WX`, `G`, `R` and `W` also accept a path
that stops.
