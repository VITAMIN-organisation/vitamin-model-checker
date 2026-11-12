# File Formats

This page describes the **model and formula file conventions** used by
`vitamin-model-checker`. It is for people creating examples, fixtures, or VMI
bundles. It does not define operator denotations; those live in
[logic_knowledge_base.md](logic_knowledge_base.md) and per-logic
`docs/<Logic>/algorithm.md` pages.

## Model Files

Model files are plain `.txt` files. Generic loaders detect a type from section
headers and, for ICTL, from birelational `Transition` cell tokens (`P` / `P,R`).
When checking a formula, the engine also uses the logic metadata `model_type`
(for example ICTL always loads `BirelationalMatrix`).

Use a simple file name such as:

```text
atl_game.txt
cotl_model.txt
```

## Supported Model Types

| Model type | Used by | What it adds / how detected |
|---|---|---|
| `CGS` | ATL, CTL, LTL, NatATL, NatSL, ... | Standard concurrent game structure (default when no extension headers). |
| `BirelationalMatrix` | ICTL | Same sections as CGS; `Transition` cells are `0`/`R`/`P`/`P,R`. Detected when Transition rows use only those cells and include `P` or `P,R`; ICTL metadata also forces this type. |
| `BCGS` | IATL | CGS transitions plus boolean `Preorder` section (detected when `Preorder` is present). |
| `costCGS` | OATL, OL, RBATL, RABATL | Cost/resource information for actions and transitions. |
| `capCGS` | CapATL | Capability declarations and assignments. |
| `WalletCGS` | Wallet_ATL | Per-state wallet balances for each agent. |
| `timedCGS` | TOL, TCTL | Clocks, clock constraints, and invariants on top of costCGS. |
| `ObstructionModel` | COTL | Graph with demons that disable edges; no agents (detected by `Number_of_demons`). See [ObstructionModel Sections](#obstructionmodel-sections-cotl). |

## CGS Sections

A basic CGS model usually contains these sections:

1. `Transition`
2. `Unknown_Transition_by` (optional, for partial models)
3. `Name_State`
4. `Initial_State`
5. `Atomic_propositions`
6. `Labelling`
7. `Number_of_agents`
8. `Agent_labels` (optional display names for agents 1..n)

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

Agent_labels
Tianji Opponent
```

### `Agent_labels`

Optional whitespace-separated display names for agents. Label *i* refers to
agent *i* (1-based), in the same order as joint-action columns. Formulas still
use numeric coalitions such as `<1>` and `<2>`; labels do not change
verification semantics. When omitted, agents are shown as `1`, `2`, ...

Each label must match `[a-zA-Z0-9_-]+`. The number of labels must equal
`Number_of_agents`.

### `Transition`

The transition matrix is square: one row and one column per state.

Accepted cell values:

- `0`: no transition,
- a joint action profile for all agents (see formats below),
- a comma-separated list of joint profiles such as `AC,AD` or `A|C,A|D`,
- `*`: wildcard, meaning any joint action allows the transition.

**Joint action formats** (equivalent; both encode one move per agent, in agent order 1..n):

| Form | Example (2 agents) | Meaning |
|---|---|---|
| Compact | `AC` | Agent 1 plays `A`, agent 2 plays `C` (one character per agent). |
| Explicit | `A\|C` or `IDLE\|MOVE` | Same per-agent vector; use `\|` when action names are longer than one character. |

Algorithms normalize every profile to the explicit `|`-separated form before coalition masking and strategy pruning. Compact and explicit cells therefore have the same verification semantics. Joint profiles must match `Number_of_agents`.

The cell wildcard `*` is treated as a profile with `*` in every agent position.

Every state must have at least one outgoing transition (total / serial relation).
Use a self-loop such as `*` on terminal states. Models that leave a row entirely
`0` are rejected at load time. CTL/ATL-style operators assume infinite paths
(Baier/Katoen); without a successor, next-time modalities are ill-defined and
universal next can hold vacuously. A self-loop models a terminal situation as
"remain forever."

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

`capCGS` adds capability information for CapATL:

```text
Capacities
c cap cop
Capacities_assignment
1 0 0
1 0 0
0 1 1
Actions_for_capacities
c A B
cap A
cop B
```

- `Capacities` - space-separated capacity/resource names.
- `Capacities_assignment` - `agents x capacities` matrix of `0`/`1` values.
  Row `i` is agent `i`; column `j` is capacity `j` (same order as `Capacities`).
- `Actions_for_capacities` - one line per capacity: `capacity_name action1 action2 ...`
  listing actions associated with that capacity.

Use this format for CapATL-style capability reasoning.

## WalletCGS Sections

`WalletCGS` extends CGS with a `Wallets` section. Each line maps a state to
one balance per agent. Every state needs a row; a state without one is a load
error that names it. Example:

```text
Wallets
s0: 100 50
s1: 80 60
```

Use this format for Wallet_ATL models. Action strings can include wallet-aware
codes such as `D20` (deposit) or `B50` (bid). They are longer than one character,
so write the joint profile in the explicit form with `|` (see the cell formats in
[CGS Sections](#cgs-sections)): `D20|0` means agent 1 deposits 20 and agent 2 plays
the neutral action `0`. Which moves are available depends on the wallets; see
[Wallet_ATL](Wallet_ATL/algorithm.md#semantic-denotations).

## BirelationalMatrix Sections (ICTL)

ICTL reuses the CGS section layout (`Transition`, `Name_State`,
`Initial_State`, `Atomic_propositions`, `Labelling`; `Number_of_agents` optional
and defaults to `1`). Cells in `Transition` are relation labels, not joint
actions:

| Cell | Meaning |
|---|---|
| `0` | no relation |
| `R` | transition only |
| `P` | knowledge preorder only |
| `P,R` | both (typical diagonal) |

Prefer `P` or `P,R` on the diagonal. Bare `*` is a CGS idle convention and is
not a valid ICTL preorder marker. Full validation (C1/C2 and frame rules):
[ICTL/algorithm.md](ICTL/algorithm.md).

## BCGS Sections (IATL)

IATL models are CGS files with an extra boolean `Preorder` matrix:

```text
Transition
...
Preorder
1 1
0 1
...
```

`Transition` cells use ordinary joint-action strings. `Preorder` entries are
`0` or `1`. Detected when a `Preorder` header is present. Details:
[IATL/algorithm.md](IATL/algorithm.md).

## timedCGS Sections

`timedCGS` extends costCGS with three timed sections:

- `Clocks` - clock names used in the model,
- `Clock_constraints` - per-transition clock resets and bounds,
- `Invariants` - clock invariants per state.

An invariant is `<clock><op><integer>` with `<op>` either `<=` or `<`, and several
can share a cell, separated by commas (`x<=5,y<3`). Time can pass in a state only while
its invariant holds. Under `x<3` the clock never reaches 3, while under `x<=3` it
reaches 3 exactly and cannot go past it. This follows the delay rule of AAMAS 2025
(weighted timed automata): a delay `d` is allowed iff `v + d` satisfies the invariant.
Use `>=` guards in `Clock_constraints`, not in `Invariants`.

Comment lines (`#` or `//`) are allowed in these sections, as in the others.

TOL and TCTL share this model type. Integrate TOL before TCTL if both land in
the same branch, so `timed_cgs` is present once.

## ObstructionModel Sections (COTL)

A COTL model has no agents: it is a graph whose edges k demons can disable.
It keeps `Name_State`, `Initial_State`, `Atomic_propositions` and `Labelling`
from CGS, and adds three sections. It is detected by `Number_of_demons`.

```text
Transition
0 1 1
0 0 0
0 0 0
Name_State
s0 s1 s2
Initial_State
s0
Atomic_propositions
p
Labelling
0
1
0
Number_of_demons
2
Demon_actions
1 s0 cut_bad 1
2 s0 cut_good 1
Curses
s0 cut_bad,* s2
s0 *,cut_good s1
s0 cut_bad,cut_good s1 s2
```

| Section | Line format | Rules |
|---|---|---|
| `Transition` | `0`/`1` per cell | Row `i` marks the successors of state `i`. A state may have no successor. |
| `Number_of_demons` | `k` | One integer `>= 1`. |
| `Demon_actions` | `demon state action cost` | One line per action other than idle; `cost >= 1`. The idle action `*` is available to every demon at every state at cost 0 and is not listed. |
| `Curses` | `state a1,...,ak successor...` | One action per demon, `*` for idle. The curse disables the edges from `state` to the listed successors, which must be edges of `Transition`. A curse that is not listed disables nothing. |

Unknown states, demons or actions, a curse listed twice, a cost below 1, and a
disabled edge that is not in `Transition` are rejected with the line number.
Semantics: [COTL/algorithm.md](COTL/algorithm.md).

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
| COTL | `<1,3><1> G !q` or `<><0> X p` | ObstructionModel |
| CapATL | `<{1}> F g` | capCGS |
| Wallet_ATL | `<<1>>X auction_active` | WalletCGS |
| ICTL | `EX e` or `AG (p -> EF q)` | BirelationalMatrix |
| IATL | `<1>G a` or `[1,2]F goal` | BCGS |
| TCTL | `AG a` or `EF crossing` | timedCGS |
| TOL | `{J5}F a` | timedCGS |

Common boolean operators:

- `!` for not,
- `&&` for and,
- `||` for or,
- `->` for implication,
- `true` and `false` constants.

## Practical Rules

- End every formula with `;`.
- Start proposition, clock and capacity names in a formula with a lowercase
  letter, for example `ready` or `goal_reached`; capitals may follow (`goalA`).
  `Goal` is an error (see the
  [Atomic Proposition Policy](logic_knowledge_base.md#atomic-proposition-policy)).
- Avoid reserved words such as `and`, `or`, `F`, `G`, and `exists`.
- Comments are allowed with `#` or `//`.
- Multi-line formulas are fine as long as the final formula has a semicolon.

When adding examples for a new logic, keep the first model small. Small examples
are easier to debug and make better validation fixtures for VMI bundles.
