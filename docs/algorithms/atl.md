# ATL algorithm

The ATL checker decides `<A> phi`: can coalition `A` force `phi`, whatever the
other agents do? It runs on a `CGS` model. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#syntax-cards), the model
file in [CGS sections](../reference/file_formats.md#cgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers).
Each coalition operator is computed from the coalition pre-image, once for `X` and
as a [fixpoint](index.md#overview) for `F`, `G` and `U`.

## Coalition pre-image

`Pre(Z)` is the set of states from which the coalition can force the next state
into `Z`. A state `s` is in `Pre(Z)` when:

1. the coalition has a move `m` at `s` (one action per member);
2. every joint action at `s` that contains `m`, whatever the other agents play,
   leads only to states in `Z`.

A state with no outgoing transition has no coalition move, so it is never in
`Pre(Z)`.

## Operators

`[[phi]]` is the set of states where `phi` holds.

**Table 1: ATL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<A> X phi` | `Pre([[phi]])` | (no iteration) |
| `<A> F phi` | least fixpoint of `Z = Z \| Pre(Z)` | `[[phi]]` |
| `<A> G phi` | greatest fixpoint of `Z = Pre(Z) & [[phi]]` | all states |
| `<A> (phi U psi)` | least fixpoint of `Z = Z \| (Pre(Z) & [[phi]])` | `[[psi]]` |
