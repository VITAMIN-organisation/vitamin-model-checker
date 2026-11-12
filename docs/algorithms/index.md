# Algorithm design

This page explains the implementation choices shared by the explicit checkers:
what each technique does, which logics use it and why those logics need it. It
is for a developer who wants the reasons behind the code before reading it. Each
logic has its own page in this folder with its denotations; the logics are
introduced in the [knowledge base](../reference/logic_knowledge_base.md), and
the algorithm pattern of each one is in its
[logic comparison matrix](../reference/logic_knowledge_base.md#logic-comparison-matrix).

## Overview

Most checkers compute a set of states by repeating one step until the set stops
changing (a fixpoint). The step is a pre-image: the states from which a move
leads into a given set (for a coalition, a move the coalition can force). It
looks at the moves out of every state, so a fixpoint over `n` states can scan
the whole model up to `n` times. Most techniques below make that repeated scan
cheaper; the rest exist because a logic cannot be checked state by state at all
(timed and strategy-based logics). Table 1 lists them:

**Table 1: Techniques, the logics that use them, and why.**

| Technique | Logics | Why these logics need it |
| :--- | :--- | :--- |
| Move cache | ATL, ATLF, IATL, Wallet_ATL, RBATL, RABATL, OATL, COTL | Their fixpoints read the moves of every state on every round |
| Bit-vector sets | ATL, Wallet_ATL, RBATL, RABATL | The same rounds ask "is this state in the set?" many times on large models |
| Early stop | ATL, Wallet_ATL | Their `F` and `U` fixpoints only grow, so known states need no recheck |
| Subformula memo | RBATL, RABATL, OATL, OL | Their solvers may meet the same subformula twice |
| Per-check caches | CapATL | Capacity and knowledge lookups repeat within one check |
| Upward closure | ICTL, IATL | Every `->` and `!` needs the states above each state in the knowledge order |
| Zone graph | TCTL, TOL | Clock values are continuous and cannot be listed |
| Obstruction filter | TOL | The Demon's budget must be checked at every step of a fixpoint |
| Strategy pruning | LTL, NatATL, NatSL | Truth depends on a strategy, so the checker searches strategies |
| Performance tests | ATL, CTL, OATL and others | A change to a cache or step can slow the checker without failing a test |

## Move cache

The checker reads the transition matrix once and keeps, for each state, its
outgoing joint actions (one action per agent). Every later fixpoint round reads
this list instead of decoding the matrix again. The cost of one round stays the
same order; the repeated decoding is what goes away.

The logics differ in what they store:

- ATL and Wallet_ATL: one flat cache for the whole check; the pre-image groups a
  state's moves by what the coalition plays when it visits that state.
  Wallet_ATL keeps only the moves the agents can pay for.
- IATL: one cache per coalition, built the first time that coalition appears.
- ATLF, RBATL and RABATL: one cache per operator, grouped by its coalition.
- OATL: each joint action is stored with its cost, since the Demon (the player
  that erases joint actions) chooses by what erasing costs.
- COTL: per legion (the set of demons that disable edges together), the
  legion's actions with their cost and the successors the other demons can
  leave. Legion actions that no listed curse (joint demon action) extends all
  leave every edge, so only the cheapest of them is kept; the work then follows
  the number of listed curses instead of the number of joint actions, which
  grows exponentially with the number of demons.

## Bit-vector sets

From 300 states upward, the target set of the fixpoint, the set the pre-image
tests successors against, is a bit array instead of a Python set. A pre-image
asks "is this successor in the set?" for every move it scans, and an indexed bit
test is cheaper than a hash lookup on large sets. Below 300 states the setup
cost of the array is larger than the gain, so plain sets stay. ATL uses it, and
so does Wallet_ATL through the ATL pre-image; RBATL and RABATL use it through
their shared pre-image.

## Early stop

During a least fixpoint for `F` or `U` the set only grows, so a state already in
it will stay there. The pre-image skips such states instead of enumerating their
coalition moves again. ATL and Wallet_ATL use it in their `F` and `U` fixpoints.

## Subformula memo

While walking the formula tree, the result of each subformula is stored and
reused if the same subformula appears again in the same check. RBATL and RABATL
use it through the bounded ATL solver they share, and OATL through its own
solver, which OL also runs.

## Per-check caches (CapATL)

CapATL looks up state positions and capacity and knowledge combinations many
times within one check, so it caches them. The caches are cleared at the start
of each check, because a result computed for one model or formula must not be
reused for the next.

## Upward closure (ICTL, IATL)

In the intuitionistic logics a state's truth depends on all states above it in
the knowledge order `P` (see [ICTL](ictl.md#model)): `->` and `!` hold at a
state only if they hold at every state above it. The checker computes, once per
model, the set of states above each state, instead of following `P` again for
every connective.

## Zone graph (TCTL, TOL)

A timed model has clocks with real values, so its states cannot be listed one by
one. The checker groups clock values that behave the same into zones and builds
a finite graph of (location, zone) nodes, called regions in the TCTL page, with
edges for time passing and for discrete moves. Formula clocks, the clocks a
formula resets with a freeze (`j . phi`) or tests in a guard, are added to the
graph as extra clocks. TCTL runs its fixpoints on the regions of this graph; TOL
uses it for the timed backward step.

## Obstruction filter (TOL)

A TOL step keeps the predecessors of a set where the Demon can block every edge
leaving the set within the budget (Definition 15 of the TOL paper, AAMAS 2025;
see [TOL](tol.md#semantic-denotations)). The checker computes it as a set
operation on locations, using the zone graph only for a step under a clock
guard, instead of exploring the game tree at each step, so the fixpoints of TOL
stay ordinary set iterations.

## Strategy pruning (LTL, NatATL, NatSL)

In these logics a formula holds if some bounded strategy makes it hold, so the
checker enumerates strategies, removes from the model the moves each one
forbids, and checks the goal on what remains.

- Memoryless strategies (LTL, NatATL): the pruning removes moves from the
  transition matrix. Many strategies share the same conditions, so the result
  of a condition on a model is cached and reused across candidates.
- Recall strategies (NatATL): the pruning works on a tree of histories, with the
  same condition cache.
- NatSL: an action a strategy selects must be available where the strategy
  applies; otherwise the strategy is rejected, with no fallback to an idle move.
  NatSL has no condition cache.

## Performance tests

Timed checks on generated models (100 and 200 states for ATL and OATL, larger in
the scalability suites) catch a change that slows a pre-image, a cache or a
fixpoint. Their time limits are regression guards, not complexity claims.
