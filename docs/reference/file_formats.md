# File formats

This page describes the model and formula file conventions used by
`vitamin-model-checker`. It is for people creating examples, fixtures, or VMI
bundles. It does not define operator denotations; those live in
[logic_knowledge_base.md](logic_knowledge_base.md) and the per-logic pages in
[docs/algorithms/](../algorithms/index.md).

## Contents

- [Model files](#model-files)
- [Supported model types](#supported-model-types)
- [CGS sections](#cgs-sections)
- [costCGS sections](#costcgs-sections)
- [capCGS sections](#capcgs-sections)
- [WalletCGS sections](#walletcgs-sections)
- [BirelationalMatrix sections (ICTL)](#birelationalmatrix-sections-ictl)
- [BCGS sections (IATL)](#bcgs-sections-iatl)
- [timedCGS sections](#timedcgs-sections)
- [ObstructionModel sections (COTL)](#obstructionmodel-sections-cotl)
- [Formula files](#formula-files)
- [Formula syntax overview](#formula-syntax-overview)
- [Practical rules](#practical-rules)

## Model Files

Model files are plain `.txt` files. The loader detects a type from the section
headers and, for ICTL, from the `Transition` cells; the rules are in
[Table 1](#supported-model-types).

Use a simple file name such as:

```text
atl_game.txt
cotl_model.txt
```

## Supported Model Types

Table 1 lists each model type, the logics that use it, what it adds and how the
loader detects it. The loader tests the rows in the table's order and takes the
first that matches (`detect_model_type_from_content` in
`model_checker/models/model_factory.py`), so a file with both `Wallets` and
`Costs_for_actions` is a WalletCGS. A header matches when it stands alone on a
line, spaces around it ignored:

**Table 1: Supported model types, in detection order.**

| Model type | Used by | What it adds | Detected when |
| :--- | :--- | :--- | :--- |
| [`ObstructionModel`](#obstructionmodel-sections-cotl) | COTL | Graph with demons that disable edges; no agents. | A `Number_of_demons` header |
| [`WalletCGS`](#walletcgs-sections) | Wallet_ATL | Per-state wallet balances for each agent. | A `Wallets` header |
| [`timedCGS`](#timedcgs-sections) | TOL, TCTL | Clocks, clock constraints and invariants on top of costCGS. | A `Clocks` or `Clock_constraints` header |
| [`costCGS`](#costcgs-sections) | OATL, OL, RBATL, RABATL | Costs of actions or edges. | A `Transition_With_Costs`, `Costs_for_actions` or `Costs_for_actions_split` header |
| [`capCGS`](#capcgs-sections) | CapATL | Capacity declarations and assignments. | A `Capacities` or `Capacities_assignment` header |
| [`BCGS`](#bcgs-sections-iatl) | IATL | CGS transitions plus a boolean `Preorder` section. | A `Preorder` header |
| [`BirelationalMatrix`](#birelationalmatrix-sections-ictl) | ICTL | Same sections as CGS; `Transition` cells are `0`/`R`/`P`/`P,R`. | Every `Transition` cell is one of those four and at least one is `P` or `P,R` |
| [`CGS`](#cgs-sections) | ATL, CTL, LTL, NatATL, NatSL, ... | Standard concurrent game structure. | No row above matches |

When checking a formula, the logic's `model_type` metadata also sets the type, so
ICTL always loads a `BirelationalMatrix`.

## CGS Sections

A basic CGS model usually contains these sections:

1. `Transition`
2. `Unknown_Transition_by` (optional; the loader reads it into
   `unknown_transition_matrix`, and no checker uses it)
3. `Name_State`
4. `Initial_State`
5. `Atomic_propositions`
6. `Labelling`
7. `Number_of_agents`
8. `Agent_labels` (optional display names for agents 1..n)

Section headers are case-sensitive. A line that starts with `#` or `//` is a
comment in every section except the BCGS `Preorder`; text after data on the same
line is not a comment.

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

Table 2 shows the two joint action formats. They are equivalent: both encode one
move per agent, in agent order 1..n.

**Table 2: Joint action formats.**

| Form | Example (2 agents) | Meaning |
| :--- | :--- | :--- |
| Compact | `AC` | Agent 1 plays `A`, agent 2 plays `C` (one character per agent). |
| Explicit | `A\|C` or `IDLE\|MOVE` | Same per-agent vector; use `\|` when action names are longer than one character. |

Algorithms normalize every profile to the explicit `|`-separated form before coalition masking and strategy pruning. Compact and explicit cells therefore have the same verification semantics. A joint profile has exactly `Number_of_agents` actions (`parse_joint_action_cell` in `cgs_actions.py`), because a missing or extra action would move every later action to the wrong agent.

A profile with too few or too many actions still loads. It fails when a checker reads the actions. For example, with 2 agents and the too-short cell `A`, ATL reports "Action joint 'A' in cell 'A' has 1 action(s); expected 2 (one per agent).". CTL does not read actions, so on such a file it returns a result.

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

`costCGS` extends CGS for cost-aware logics. A file is read as costCGS when it has
any of these three sections:

- `Costs_for_actions`: one line per joint action, `action state$cost[:cost...]`.
  Several states share a line, joined by `;`: `AA s0$1:1;s2$1:1`. The values after
  `$`, separated by `:`, form the cost vector: value `i` is the cost in resource
  `i`, and RBATL compares it with bound `i` of the formula. A line with a third
  token or a negative cost is an error.
- `Costs_for_actions_split`: the same line, with each `:`-separated group split
  again by `,` into one cost per agent: in `AA s0$1,2:3,4`, agents 1 and 2 pay 1 and
  2 of resource 1, and 3 and 4 of resource 2. RABATL adds the costs of the coalition's
  agents for each resource.
- `Transition_With_Costs`: replaces `Transition`; a square matrix whose cells are
  edge costs, `0` for no edge. It gives no actions, so OATL accepts it only for a
  coalition of all agents and otherwise reports "a Transition_With_Costs model gives
  only edge costs; use Transition with Costs_for_actions" (`OATL/preimage.py`).

Examples:

```text
Costs_for_actions
AA s0$1:5
```

```text
Costs_for_actions_split
AA s0$1,2:3,4
```

```text
Transition_With_Costs
0 3
4 0
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

- `Capacities`: space-separated capacity/resource names. A name follows the
  [name rule](logic_knowledge_base.md#names-and-keywords) (`[a-z][a-zA-Z0-9_]*`,
  not a reserved word), and is not `kcap` or `kcap` with digits (`kcap1`), which
  CapATL reads as its knowledge operator.
- `Capacities_assignment`: `agents x capacities` matrix of `0`/`1` values.
  Row `i` is agent `i`; column `j` is capacity `j` (same order as `Capacities`).
- `Actions_for_capacities`: one line per capacity, `capacity_name action1 action2 ...`,
  listing the actions that capacity enables (`CapATL/combinatorics.py`).

Use this format for CapATL-style capability reasoning.

## WalletCGS Sections

`WalletCGS` extends CGS with a `Wallets` section. Each line maps a state to
one balance per agent: the state, then each balance after its own `:`
(`s0: 100 : 50`). A balance is a natural number. Two balances separated by a space
only are read as one value, so `s0: 100 50` fails with "Wallet value '100 50' is
not a natural number in 's0: 100 50'.". Every state needs a row; a state without
one fails with "Wallets has no row for state(s) s0; every state needs one balance
per agent.". Example for 2 agents:

```text
Wallets
s0: 100 : 50
s1: 80 : 60
```

Use this format for Wallet_ATL models. An action can carry an amount, such as
`D20` or `W20`; which letters cost money and which never do is in
[payable moves](../algorithms/wallet_atl.md#payable-moves). These actions are longer
than one character, so write the joint profile in the explicit form with `|` (see
the cell formats in [CGS sections](#cgs-sections)): `D20|0` means agent 1 plays
`D20` and agent 2 plays the neutral action `0`.

## BirelationalMatrix Sections (ICTL)

ICTL reuses the CGS section layout (`Transition`, `Name_State`,
`Initial_State`, `Atomic_propositions`, `Labelling`; `Number_of_agents` optional
and defaults to `1`). Cells in `Transition` are relation labels, not joint
actions; Table 3 lists them:

**Table 3: ICTL `Transition` cells.**

| Cell | Meaning |
| :--- | :--- |
| `0` | no relation |
| `R` | transition only |
| `P` | knowledge preorder only |
| `P,R` | both (typical diagonal) |

Every diagonal cell must be `P` or `P,R`, because the order `P` is reflexive;
otherwise ICTL reports "The graph is not reflective." (reflexive) Bare `*` is a CGS idle
convention and is not a valid ICTL preorder marker. Full validation (C1/C2 and frame rules):
[ICTL algorithm](../algorithms/ictl.md).

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
`0` or `1`. Detected when a `Preorder` header is present. Each diagonal
`Transition` cell must hold the idle self-loop (`II,II` for 2 agents); otherwise
IATL reports "There's no Idle from some states and some agents". A comment line
inside `Preorder` is an error, unlike in the other sections (for a `#` line:
"invalid literal for int() with base 10: '#'"). Details: [IATL algorithm](../algorithms/iatl.md).

## timedCGS Sections

`timedCGS` extends costCGS with three timed sections:

- `Clocks`: the clock names, separated by spaces, on one line or several, which
  follow the [name rule](logic_knowledge_base.md#names-and-keywords).
- `Clock_constraints`: per-transition clock resets and bounds.
- `Invariants`: clock invariants per state.

`Clock_constraints` is a states x states matrix like `Transition`: the cell in row `s`,
column `t` constrains the transition from `s` to `t`. Cells are separated by spaces.
A cell holds `<clock><op><integer>` tokens separated by commas, with
`<op>` one of `>=`, `<=`, `==`, `>`, `<` for a bound, or `=` for a reset (`x=0`).
`0`, `-` and `*` mean no constraint. Example for 2 states and clock `x`:

```text
Clocks
x
Clock_constraints
x<=1 x>=2,x=0
0 x<=1
```

An invariant is `<clock><op><integer>` with `<op>` either `<=` or `<`, and several
can share a cell, separated by commas (`x<=5,y<3`). Time can pass in a state only while
its invariant holds. Under `x<3` the clock never reaches 3, while under `x<=3` it
reaches 3 exactly and cannot go past it. This follows the delay rule of AAMAS 2025
(weighted timed automata): a delay `d` is allowed iff `v + d` satisfies the invariant.
Use `>=` guards in `Clock_constraints`, not in `Invariants`.

Comment lines (`#` or `//`) are allowed in these sections, as in the CGS sections.

TOL and TCTL share this model type.

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

Table 4 gives the line format and rules of each section:

**Table 4: ObstructionModel sections.**

| Section | Line format | Rules |
| :--- | :--- | :--- |
| `Transition` | `0`/`1` per cell | Row `i` marks the successors of state `i`. A state may have no successor. |
| `Number_of_demons` | `k` | One integer `>= 1`. |
| `Demon_actions` | `demon state action cost` | One line per action other than idle; `cost >= 1`. The idle action `*` is available to every demon at every state at cost 0 and is not listed. |
| `Curses` | `state a1,...,ak successor...` | One action per demon, `*` for idle. The curse disables the edges from `state` to the listed successors, which must be edges of `Transition`. A curse that is not listed disables nothing. |

Unknown states, demons or actions, a curse listed twice, a cost below 1, and a
disabled edge that is not in `Transition` are rejected with the line number.
Semantics: [COTL algorithm](../algorithms/cotl.md).

## Formula Files

This package reads one formula string per call and does not read formula files;
the VITAMIN Workbench reads them (`vitamin_api/features/model_checking/services/processing/formula_parser.py`
in the vitamin-workbench repository). The rules below are the Workbench's.

Formula files usually sit next to their model file and use the
`_formula.txt` suffix:

```text
cotl_model.txt
cotl_model_formula.txt
```

This naming pattern helps tools pair formulas with models.

A formula file holds one or more formulas. Each ends with `;`, except the last,
which may omit it. A line holds at most one `;`, with nothing but a comment after it, so two
formulas never share a line; one formula may span several lines. A repeated label
or a repeated formula is an error that names the line.

```text
MainProp: <1> F win;
SafetyCheck: <1,2> G safe;
AG (request -> AF grant);
```

Labels are optional. If used, a label must be an identifier followed by `:`.
The first formula is treated as the primary formula by tools that need one.

## Formula Syntax Overview

The prefix, operators, model type and one example formula of each logic are in the
[syntax cards](logic_knowledge_base.md#syntax-cards). The connectives (`!`, `&&`,
`||`, `->`) and the constants `true` and `false` are in
[Boolean Logic](logic_knowledge_base.md#boolean-logic-shared-syntax).

## Practical Rules

- Formula files: `;` and line rules are in [formula files](#formula-files).
- Proposition, clock and capacity names, in models and formulas, start with a
  lowercase letter (`ready`, `goal_reached`, `goalA`; `Goal` is an error), and the
  reserved words (`until`, `exist`, `true`, ...) are never names, in any letter
  case. This is the name rule; the full rules and list are in
  [names and keywords](logic_knowledge_base.md#names-and-keywords).
- In a formula file, `#` or `//` starts a comment that runs to the end of the line.

When adding examples for a new logic, keep the first model small. Small examples
are easier to debug and make better validation fixtures for VMI bundles.
