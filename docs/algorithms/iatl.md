# IATL algorithm

The IATL checker decides ATL formulas in which truth may only grow as knowledge
grows. Its model is a CGS with a second relation `P` on the states
(`s <=_P t`: `t` knows at least what `s` knows), written as a 0/1 matrix in the
`Preorder` section. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#iatl---intuitionistic-atl),
the model file in [BCGS sections](../reference/file_formats.md#bcgs-sections-iatl).

## Model checks

The model is rejected at load time, with a message that names the failed
condition, unless:

- every agent has actions, every state has an outgoing transition, and every
  diagonal cell holds the idle self-loop (`II,...`);
- `P` is reflexive, antisymmetric and transitive;
- for every non-empty coalition, C1 (forward simulation of coalition moves along
  `P`) and C2 (the dual, backward) hold;
- labelling is monotone: `s <=_P s'` implies that `s'` has every atom of `s`.

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers),
except for `!` and `->`, which use the upward closure `^up` described in
[ICTL](ictl.md#overview).

`<A>` is the existential coalition and `[A]` the universal one, each with its own
pre-image:

- `PreD(Z)`, for `<A>`: the [ATL pre-image](atl.md#coalition-pre-image).
- `PreF(Z)`, for `[A]`: the states that have moves and where every move of `A` has
  some move of the other agents leading into `Z`.

## Operators

`Pre` below is `PreD` under `<A>` and `PreF` under `[A]`; `[[phi]]` is the set of
states where `phi` holds and `S` the set of all states.

**Table 1: IATL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `!phi` | `(S - [[phi]])^up` | (no iteration) |
| `phi -> psi` | `((S - [[phi]]) \| [[psi]])^up` | (no iteration) |
| `<A> X phi`, `[A] X phi` | `Pre([[phi]])` | (no iteration) |
| `F phi` | least fixpoint of `Z = Z \| Pre(Z)` | `[[phi]]` |
| `G phi` | greatest fixpoint of `Z = Pre(Z) & [[phi]]` | `S` |
| `(phi U psi)` | least fixpoint of `Z = Z \| (Pre(Z) & [[phi]])` | `[[psi]]` |
| `(phi R psi)` | greatest fixpoint of `Z = [[psi]] & ([[phi]] \| Pre(Z))` | `S` |

`^up` is applied only to `!` and `->`. `[A]` is not computed through `<A>` and
`!`, and `G` not through `F` and `!`: each operator has its own fixpoint.

Example: two agents that only idle; `s0` loops, `s1` loops, `s2` goes to `s1`
or itself; `P` orders `s0 <=_P s1 <=_P s2`, and only `s2` is labelled `p`.
`!(<1,2> X p) && !(<1,2> X !p)` holds at `s0`, `s1` and `s2`. Every state has
`s2` above it, so `!p` holds nowhere and `<1,2> X !p` holds nowhere; `<1,2> X p`
holds nowhere either, since the one move of `s2` may lead to `s1`. With `!` as
the plain complement, as in [ATL](atl.md), `!p` would hold at `s0` and `s1`, so
`<1,2> X !p` would hold there and the formula would hold only at `s2`.
