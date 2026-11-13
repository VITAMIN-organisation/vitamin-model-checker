# CTL algorithm

The CTL checker decides `E` and `A` path formulas, such as `AG safe` or
`E(p U q)`, on a `CGS` model read as a plain transition graph: there is an edge
from `s` to `t` when some joint action leads from `s` to `t`. Formula syntax is in
the [knowledge base](../reference/logic_knowledge_base.md#ctl---computation-tree-logic),
the model file in [CGS sections](../reference/file_formats.md#cgs-sections).

## Overview

The checker follows the [shared steps](index.md#steps-shared-by-the-set-based-checkers).
Each temporal operator is computed from one of two
[pre-images](index.md#overview), once for `X` and as a
[fixpoint](index.md#overview) for the others:

- `PreE(Z)`: the states with at least one successor in `Z`.
- `PreA(Z)`: the states that have successors and whose successors are all in `Z`.

## Operators

`[[phi]]` is the set of states where `phi` holds and `S` the set of all states.

**Table 1: CTL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `EX phi` | `PreE([[phi]])` | (no iteration) |
| `AX phi` | `PreA([[phi]])` | (no iteration) |
| `EF phi` | least fixpoint of `Z = Z \| PreE(Z)` | `[[phi]]` |
| `EG phi` | greatest fixpoint of `Z = [[phi]] & PreE(Z)` | `S` |
| `AF phi` | `S` minus the set of `EG !phi` | (that of `EG`) |
| `AG phi` | `S` minus the set of `EF !phi` | (that of `EF`) |
| `E(phi U psi)` | least fixpoint of `Z = Z \| ([[phi]] & PreE(Z))` | `[[psi]]` |
| `A(phi U psi)` | least fixpoint of `Z = Z \| ([[phi]] & PreA(Z))` | `[[psi]]` |

## Traces

CTL is the only checker that can return a path explaining the result. With the
`generate_trace` option on, it returns one path for the outermost operator:

- a witness when an `E` formula holds at the initial state (for `EX`, `EF`, `EU`,
  `EG`);
- a counterexample when an `A` formula fails there (for `AX`, `AG`, `AF`, `AU`).

`EG`, `AF` and `AU` can need a path that ends in a loop; it is returned as a lasso
with the index where the loop starts. There is no trace for a false `E` formula,
a true `A` formula, a formula whose outermost part is a connective or an atom, or
a path longer than 100 states. With the option on, the result also has the fields
`satisfied`, `states`, `trace`, `strategy` and `metadata`.
