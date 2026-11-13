# ICTL algorithm

The ICTL checker decides CTL formulas in which truth may only grow as knowledge
grows. Its model has two relations on one set of states `S`: `R`, the transitions,
and `P` (`s <=_P t`: `t` knows at least what `s` knows). Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#ictl---intuitionistic-ctl),
the model file in
[BirelationalMatrix sections](../reference/file_formats.md#birelationalmatrix-sections-ictl).

## Model checks

The model is rejected at load time, with a message that names the failed
condition, unless:

- `R` is serial (every state has a successor) and the matrix is square;
- `P` is reflexive, antisymmetric and transitive;
- labelling is monotone: `s <=_P s'` implies that `s'` has every atom of `s`;
- C1 and C2 hold (`s -R-> t` is an `R` edge from `s` to `t`):

```text
C1: if s <=_P s' and s -R-> t,  then some t' has s' -R-> t' and t <=_P t'
C2: if s <=_P s' and s' -R-> t', then some t  has s -R-> t  and t <=_P t'
```

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers),
except for `!` and `->`. Those hold at a state only if they hold at every state
above it in `P`: for a set `Y`, `Y^up` is the set of states `s` whose whole upset
`{t | s <=_P t}` lies in `Y`. The upsets are computed once per check.

There are two [pre-images](index.md#overview): `PreE(Z)` is the set of states
with an `R` successor in `Z`; `PreA(Z)` is the set of states that have `R`
successors and whose successors are all in `Z`. `Pre` below is `PreE` under `E`
and `PreA` under `A`.

## Operators

`[[phi]]` is the set of states where `phi` holds and `S` the set of all states.
Fixpoints and `R` (release) are defined in the [overview](index.md#overview).

**Table 1: ICTL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `!phi` | `(S - [[phi]])^up` | (no iteration) |
| `phi -> psi` | `((S - [[phi]]) \| [[psi]])^up` | (no iteration) |
| `EX phi`, `AX phi` | `Pre([[phi]])` | (no iteration) |
| `EF phi`, `AF phi` | least fixpoint of `Z = Z \| Pre(Z)` | `[[phi]]` |
| `EG phi`, `AG phi` | greatest fixpoint of `Z = [[phi]] & Pre(Z)` | `S` |
| `E(phi U psi)`, `A(phi U psi)` | least fixpoint of `Z = Z \| ([[phi]] & Pre(Z))` | `[[psi]]` |
| `E(phi R psi)`, `A(phi R psi)` | greatest fixpoint of `Z = [[psi]] & ([[phi]] \| Pre(Z))` | `S` |

`^up` is applied only to `!` and `->`, not after the temporal operators. Each of
`EF`, `AF`, `EG` and `AG` has its own fixpoint: `AF phi` is not computed as the
complement of `EG !phi`, as [CTL](ctl.md) does.
