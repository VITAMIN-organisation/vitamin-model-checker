# CapATL algorithm

The CapATL checker decides `<{A}> phi` when each agent acts within a capacity: a
capacity is a named set of actions, and each agent has one capacity, taken from
those the model allows it. The checker answers whether, for some choice of
capacities, the coalition can force `phi`. It runs on a `capCGS` model. Formula
syntax is in the [knowledge base](../reference/logic_knowledge_base.md#capatl),
the model file in [capCGS sections](../reference/file_formats.md#capcgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers),
except that it computes sets of pairs (state, capacity of each agent) instead of
sets of states:

1. The pairs are every state combined with every assignment of one allowed
   capacity to each agent.
2. An atom is the set of pairs whose state is labelled with it; `!`, `&&`, `||`
   and `->` are set operations on pairs.
3. Coalition operators use the [pre-image](index.md#overview) defined below.
4. The result lists the states that appear in at least one pair of the final set,
   so a state holds if the formula holds there for some capacity assignment.

## Pre-image

A coalition move at a pair is one action per member, each allowed by that
member's capacity. A transition from the pair's state follows the move when it
agrees with the members' actions; it is kept only if every agent's action on it,
member or not, is allowed by that agent's capacity. The successor pair has the
transition's target state and the same capacities.

`Pre(Z)` is the set of (pair, coalition move) where the move has at least one kept
transition and every successor pair is in `Z`. Each operator works on such
(pair, coalition move) elements and drops the move when it passes a set to the
next subformula.

## Operators

`[[phi]]` is the set of pairs where `phi` holds, each extended with the coalition
moves allowed at the pair. Fixpoints and `R` (release) are defined in the
[overview](index.md#overview).

**Table 1: CapATL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<{A}> X phi` | `Pre([[phi]])` | (no iteration) |
| `<{A}> F phi` | least fixpoint of `Z = Z \| Pre(Z)` | `[[phi]]` |
| `<{A}> G phi` | `Z = Pre(Z) & [[phi]]` until it stops shrinking | `[[phi]]` |
| `<{A}> (phi U psi)` | least fixpoint of `Z = Z \| (Pre(Z) & [[phi]])` | `[[psi]]` |
| `<{A}> (phi R psi)` | `Z = [[psi]] & ([[phi]] \| Pre(Z))` until it stops shrinking | `[[psi]]` |

## Knowledge operator

The parser accepts the knowledge operator `Ka(cap)`, but the checker cannot
evaluate it. Checking a formula that contains it anywhere returns an error of type
`validation`: "The knowledge operator K1(...) is parsed but not evaluated by the
CapATL solver yet", with the operator's number in place of `1` (`kcap2(...)` is
reported as `K2(...)`).
