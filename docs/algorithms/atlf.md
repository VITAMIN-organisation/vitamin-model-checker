# ATLF algorithm

The ATLF checker computes, for each state, a value between 0 and 1 for an ATL
formula instead of true or false: the best value coalition `A` can guarantee,
whatever the other agents do. It accepts the same formulas as [ATL](atl.md) and
runs on a `fuzzyCGS` model: a CGS whose labels are numbers between 0 and 1. Formula
syntax is in the [knowledge base](../reference/logic_knowledge_base.md#syntax-cards),
the model file in [fuzzyCGS sections](../reference/file_formats.md#fuzzycgs-sections).

## Overview

The formula is evaluated from the innermost subformula outward, as in the
[shared steps](index.md#steps-shared-by-the-set-based-checkers), but each
subformula becomes a value per state, not a set:

1. An atom's value in a state is its cell in the labelling matrix, a number
   between 0 and 1; `true` is 1.0 and `false` 0.0 everywhere.
2. The connectives combine values state by state: `!phi` is `1 - phi`, `&&` is
   `min`, `||` is `max`, and `phi -> psi` is `max(1 - phi, psi)`.
3. Coalition operators use the [pre-image](index.md#overview) defined below.

Every step uses only `1 - x`, `min` and `max`, so every result lies between 0 and
1, and a model whose labels are all 0 or 1 gives the same states as ATL, with 1.0
for true and 0.0 for false.

## Pre-image

`Pre(v)` gives each state `s` the largest value, over the coalition's moves at
`s`, of the smallest value `v` takes on the states that move can reach, whatever
the other agents play. A state with no coalition move gets 0.0.

## Operators

`phi` below stands for the values of the subformula, and `max` and `min` apply
state by state. Each iteration stops when no value changes.

**Table 1: ATLF operators.**

| Formula | Computed as | Iteration starts from |
| :--- | :--- | :--- |
| `<A> X phi` | `Pre(phi)` | (no iteration) |
| `<A> F phi` | `Z = max(Z, Pre(Z))`, values only grow | `phi` |
| `<A> G phi` | `Z = min(Pre(Z), phi)`, values only shrink | `phi` |
| `<A> (phi U psi)` | `Z = max(Z, min(Pre(Z), phi))`, values only grow | `psi` |

When `phi` is 1 in every state, `<A> G phi` returns 1 everywhere without applying
`Pre`, even at a state with no coalition move, which `Pre` would set to 0.

## Result

`res` is `Result: ` followed by the list of `(state, value)` pairs in the model's
state order, such as `Result: [('s0', 0.2), ('s1', 0.3)]`. `initial_state` gives
the value at the initial state, such as `Initial state s0: 0.2`, not true or false.
Every value is a float. The result of `1 - x` (in `!phi` and `phi -> psi`) is
rounded to 12 decimals, so `!p` with `p = 0.7` gives `0.3` where plain float
subtraction would leave `0.30000000000000004`; labels are kept as written.
