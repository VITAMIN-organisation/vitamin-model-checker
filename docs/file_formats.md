# File Formats

This page describes the model and formula files used by
`vitamin-model-checker`. It is written for people creating examples, fixtures,
or VMI bundles.

## Model Files

Model files are plain `.txt` files. The parser detects the model type from the
section headers.

Use a simple file name such as:

```text
atl_game.txt
cotl_model.txt
```

## Supported Model Types

| Model type | Used by | What it adds |
|---|---|---|
| `CGS` | ATL, CTL, LTL, NatATL, NatSL | Standard concurrent game structure. |
| `costCGS` | OATL, OL, RBATL, RABATL, COTL | Cost/resource information for actions and transitions. |
| `capCGS` | CapATL | Capability declarations and assignments. |

## CGS Sections

A basic CGS model usually contains these sections:

1. `Transition`
2. `Unknown_Transition_by` (optional, for partial models)
3. `Name_State`
4. `Initial_State`
5. `Atomic_propositions`
6. `Labelling`
7. `Number_of_agents`

Section headers are case-sensitive.

```text
Transition
0 AA
* 0

Name_State
s0 s1

Initial_State
s0

Atomic_propositions
p q

Labelling
1 0
0 1

Number_of_agents
2
```

### `Transition`

The transition matrix is square: one row and one column per state.

Accepted cell values:

- `0`: no transition,
- a joint action string such as `AC`,
- a comma-separated list such as `A1,A2`,
- `*`: wildcard, meaning any joint action allows the transition.

Joint action strings must match `Number_of_agents`.

### State And Label Sections

- `Name_State`: space-separated state names.
- `Initial_State`: exactly one state from `Name_State`.
- `Atomic_propositions`: proposition names.
- `Labelling`: binary matrix showing which propositions hold in each state.

`Initial_State` cannot be `*`.

## costCGS Sections

`costCGS` extends CGS for cost-aware logics. It can include:

- `Costs_for_actions`: action costs by state,
- `Costs_for_actions_split`: vector costs for multi-resource logics,
- `Transition_With_Costs`: transition matrix where cells carry cost data.

Examples:

```text
Costs_for_actions
AA s0$1:5
```

```text
Costs_for_actions_split
AA s0$1,2:3,4
```

## capCGS Sections

`capCGS` adds capability information:

- `Capacities`
- `Capacities_assignment`
- `Actions_for_capacities`

Use this format for CapATL-style capability reasoning.

## Formula Files

Formula files usually sit next to their model file and use the
`_formula.txt` suffix:

```text
cotl_model.txt
cotl_model_formula.txt
```

This naming pattern helps tools pair formulas with models.

Formula files can contain multiple formulas. Each formula must end with a
semicolon.

```text
MainProp: <1> F win;
SafetyCheck: <1,2> G safe;
AG (request -> AF grant);
```

Labels are optional. If used, a label must be an identifier followed by `:`.
The first formula is treated as the primary formula by tools that need one.

## Formula Syntax Overview

| Logic | Example | Model type |
|---|---|---|
| ATL | `<1,2> F p` | CGS |
| CTL | `AG p` or `EF [p]` | CGS |
| LTL | `G (p -> F q)` | CGS |
| NatATL | `<{1,2}, 5> F p` | CGS |
| NatSL | `Ex : (x, 1) F goal` | CGS |
| OATL | `<1,2><10> (p W q)` | costCGS |
| OL | `<J10> G p` | costCGS |
| RBATL | `<1><10,5> F p` | costCGS |
| RABATL | `<1><2,2> F p` | costCGS |
| COTL | `<1,2><5> G p` | costCGS |
| CapATL | `<{1}, 3> F (K1 p)` | capCGS |

Common boolean operators:

- `!` for not,
- `&&` for and,
- `||` for or,
- `->` for implication,
- `true` and `false` constants.

## Practical Rules

- End every formula with `;`.
- Keep proposition names lowercase when possible, for example `ready` or
  `goal_reached`.
- Avoid reserved words such as `and`, `or`, `F`, `G`, and `exists`.
- Comments are allowed with `#` or `//`.
- Multi-line formulas are fine as long as the final formula has a semicolon.

When adding examples for a new logic, keep the first model small. Small examples
are easier to debug and make better validation fixtures for VMI bundles.
