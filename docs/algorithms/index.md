# Algorithm design

This folder explains how each checker computes its answer, one page per logic, for
a developer who wants to understand an algorithm without reading its code. This
page gives the terms and steps the pages share, the method of each checker, and
the speed-ups that do not change results. The syntax of every logic is in the
[knowledge base](../reference/logic_knowledge_base.md), the model files in
[file formats](../reference/file_formats.md).

## Overview

Most checkers compute the set of states where a formula holds. These terms recur
on every page:

- Joint action: one action per agent, taken together in a state; it leads to one
  successor state.
- Coalition: the agents named in the formula, such as `1,2` in `<1,2>`. A
  coalition move is one action per member; the other agents complete it into
  joint actions.
- Idle: the action that does nothing, written `I` or `IDLE` in a model (COTL
  writes it `*`).
- Demon: in OATL, OL and TOL, the one player that disables moves or edges,
  paying their cost from a budget per step. COTL has one or more demons; a
  legion, a set of them that may be empty, picks together within one budget per
  step (see [COTL](cotl.md)).
- Budget and bound: a budget limits what the Demon or a legion pays in one step
  (OATL, OL, COTL, TOL). A bound limits the players being checked: in RBATL and
  RABATL each step's cost vector must stay within the vector `b`, one value per
  resource; in NatATL, NatATLF and LTL each strategy's size is at most `k`.
- Strategy: a rule that tells an agent which action to play; a profile is one
  strategy per agent.
- Pre-image: the states from which one step can be forced into a given set `Z`.
  Each page defines who forces the step and at what cost; the page writes it
  `Pre(Z)` or a variant named after its rule.
- Fixpoint: a set computed by repeating one update of `Z` until it stops
  changing. A least fixpoint starts small and only grows (used for `F` and `U`); a
  greatest fixpoint starts large and only shrinks (used for `G`, `R` and `W`).
- `phi R psi` (release): `psi` holds until `phi` and `psi` hold together, or for
  ever. `phi W psi` (weak until): `phi U psi`, or `phi` for ever. `WX phi` (weak
  next, COTL): `phi` in the next state, or the path stops.

Table 1 lists the method of each checker:

**Table 1: Method of each checker.**

| Method | Checkers |
| :--- | :--- |
| Fixpoints of a pre-image over sets of states | [CTL](ctl.md), [ATL](atl.md), [IATL](iatl.md), [ICTL](ictl.md), [Wallet_ATL](wallet_atl.md), [RBATL](rbatl.md), [RABATL](rabatl.md), [OATL](oatl.md), [OL](ol.md), [COTL](cotl.md), [CapATL](capatl.md), [TOL](tol.md) |
| The same, over values between 0 and 1 | [ATLF](atlf.md) |
| The same, over regions (location, clock zone) | [TCTL](tctl.md) |
| Search of simple strategies, then a CTL check on the pruned model | [LTL](ltl.md), [NatATL](natatl.md), [NatATLF](natatlf.md), [NatSL](natsl.md) |
| Automaton and two-player game | [ATL*](atl_star.md) |

## Steps shared by the set-based checkers

The checkers whose pages link to this section run the same outer steps, and their
pages describe only their own operators:

1. The formula is evaluated from the innermost subformula outward; each
   subformula `phi` becomes `[[phi]]`, the set of states where it holds.
2. An atom is the set of states labelled with it.
3. `!`, `&&` and `||` are complement, intersection and union on these sets;
   `phi -> psi` is the union of the complement of `[[phi]]` with `[[psi]]`.
4. The formula holds in the model when the initial state is in the final set.

The result has four text fields: `res`, `Result: ` followed by the tuple of
states of the final set in natural order (`s2` before `s10`), as in
`Result: ('s0', 's1')`; `initial_state`, such as `Initial state s0: True`; and
`formula` and `model`, the inputs. CTL with traces on adds more fields (see
[CTL traces](ctl.md#traces)). A syntax error or an atom the model does not
declare gives an error instead.

## Speed-ups

The techniques in Table 2 make the repeated pre-image cheaper; none changes a
result.

**Table 2: Speed-ups and the checkers that use them.**

| Technique | Checkers | What it saves |
| :--- | :--- | :--- |
| Move cache | ATL, ATLF, IATL, Wallet_ATL, RBATL, RABATL, OATL, OL, COTL | The moves of each state are read from the model once, not on every round |
| Bit-vector sets | ATL, Wallet_ATL, RBATL, RABATL | From 300 states up, the target set is a bit array, so "is this state in the set?" is an index test |
| Early stop | ATL, Wallet_ATL | In `F` and `U`, a state already in the set is not tested again |
| Subformula memo | RBATL, RABATL, OATL, OL | A subformula that appears twice is computed once |
| Per-check caches | CapATL | Capacity lookups are cached within one check and cleared before the next |
| Upset table | ICTL, IATL | The [upset](ictl.md#overview) of each state (the states above it in the preorder `P`) is computed once per check, not on every round |
| Condition cache | NatATL | The states where a rule's condition holds are computed once and reused across strategies; LTL rebuilds the model for each candidate, so its cache lasts one candidate |
| Curse grouping | COTL | Legion actions that no listed [curse](cotl.md#model) extends are merged into the cheapest one, so the work grows with the listed curses, not with all joint demon actions |
