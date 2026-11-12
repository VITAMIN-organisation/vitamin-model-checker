# RBATL algorithm

The RBATL checker decides `<A><b> phi`: can coalition `A` force `phi` when every
step it takes costs at most the bound vector `b`? It runs on a `costCGS` model, where
each joint action has a cost vector in each state. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl), the model file
in [costCGS sections](../reference/file_formats.md#costcgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers):
it computes the set of states where each subformula holds and checks the initial
state. A coalition operator is computed from the bounded pre-image (next section),
once for `X` and as a [fixpoint](index.md#overview) for `F`, `G` and `U`. A
subformula that appears twice is computed once.

## Bounded pre-image

`Pre(Z)` is the set of states from which the coalition can move into `Z` within the
bound. A state `s` is in `Pre(Z)` when the coalition has a move `m` (one action per
member) such that:

1. some joint action that contains `m` leads into `Z` and its cost vector at `s` is
   within `b`: `cost_i <= b_i` for each resource `i` that `b` covers (with `b` of
   length 1, the second cost value is not limited);
2. every state that a joint action containing `m` can reach is in `Z`, whatever the
   other agents play.

Three consequences follow:

- The bound applies to each step on its own. Costs do not add up along a path, so
  a goal ten cheap steps away is as reachable as one step away.
- Only one joint action of the move has to be within the bound. The costs of the
  other agents' other choices are not checked.
- A joint action with no cost for `s` in the model never counts as within the bound.

## Operators

Table 1 lists what each operator computes; `[[phi]]` is the set of states where
`phi` holds.

**Table 1: RBATL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<A><b> X phi` | `Pre([[phi]])` | (no iteration) |
| `<A><b> F phi` | least fixpoint of `Z = Z \| Pre(Z)` | `[[phi]]` |
| `<A><b> G phi` | greatest fixpoint of `Z = Pre(Z) & [[phi]]` | all states |
| `<A><b> (phi U psi)` | least fixpoint of `Z = Z \| (Pre(Z) & [[phi]])` | `[[psi]]` |

Example: one agent; in `s0` action `A` (cost 3) leads to `s1`, where `p` holds, and
action `B` (cost 0) stays in `s0`. `<1><2> F p` gives `{s1}`: `A` costs more than 2,
so `s0` never enters the set. `<1><3> F p` gives `{s0, s1}`. `<1><2> G !p` gives
`{s0}`, since `B` keeps the agent in `s0` at cost 0.

[RABATL](rabatl.md) runs the same algorithm; only the cost of a joint action is
computed differently.
