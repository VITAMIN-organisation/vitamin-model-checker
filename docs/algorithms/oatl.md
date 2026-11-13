# OATL algorithm

The OATL checker decides `<A><n> phi` on a `costCGS` model: a Demon, the player
that disables moves at a cost, has a budget of `n` at each step and disables moves
of coalition `A` to steer the play towards `phi`; the Demon
[pre-image](index.md#overview), defined [below](#demon-pre-image), says exactly
what one step can force. Formula
syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#oatl), the model file in
[costCGS sections](../reference/file_formats.md#costcgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers).
Each temporal operator is
computed from the Demon pre-image, once for `X` and as a
[fixpoint](index.md#overview) for the others.

## Demon pre-image

A state `s` is in `Pre(Z)` when these steps succeed:

1. Group the joint actions of `s` by the coalition's part: a coalition move is one
   action per member of `A`, together with every joint action that contains it.
   Disabling a move costs the sum of the costs of its joint actions; a cost vector
   such as `1:0` counts as the sum of its values.
2. Mark every move whose successors all lie outside `Z`.
3. Some move must stay unmarked, and disabling all marked moves must cost at most
   `n`.

The unmarked moves each have at least one successor in `Z`. The budget applies to
each step on its own; costs do not add up along a path. A move of cost 0 is
disabled for free, so with `n = 0` the Demon can still disable zero-cost moves.

A joint action with no cost in the model cannot be priced. The checker computes
the result twice, once as if such actions could never be disabled and once as if
they were free. If the two results differ, the check fails with an error of type
`model` that names the operator (such as `<1><0>X`), the states and the joint
actions; otherwise the missing costs do not matter. The only joint action of a
state is never disabled, so its cost is not needed.

## Operators

`[[phi]]` is the set of states where `phi` holds. `R` and `W` are defined in the
[overview](index.md#overview).

**Table 1: OATL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<A><n> X phi` | `Pre([[phi]])` | (no iteration) |
| `<A><n> F phi` | least fixpoint of `Z = [[phi]] \| Pre(Z)` | `[[phi]]` |
| `<A><n> G phi` | greatest fixpoint of `Z = [[phi]] & Pre(Z)` | `[[phi]]` |
| `<A><n> (phi U psi)` | least fixpoint of `Z = [[psi]] \| ([[phi]] & Pre(Z))` | `[[psi]]` |
| `<A><n> (phi R psi)` | greatest fixpoint of `Z = [[psi]] & ([[phi]] \| Pre(Z))` | `[[psi]]` |
| `<A><n> (phi W psi)` | greatest fixpoint of `Z = ([[phi]] \| [[psi]]) & ([[psi]] \| Pre(Z))` | `[[phi]] \| [[psi]]` |

On a model written with `Transition_With_Costs` (one cost per edge), only the
coalition of all agents can be checked; a smaller coalition is an error of type
`model` that asks for `Transition` with `Costs_for_actions`.
