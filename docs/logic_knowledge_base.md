# Logic knowledge base

This is the cross-logic theory and syntax map for VITAMIN, for a developer who
writes formulas in several logics or [adds a logic](adding_a_new_logic.md). The
per-logic `docs/<Logic>/algorithm.md` pages (for example
[ICTL/algorithm.md](ICTL/algorithm.md)) hold denotations, fixpoints, validation
proofs and pipeline details, and [file_formats.md](file_formats.md) says how to
author `.txt` models.

## Contents

- [Overview](#overview)
- [Per-logic algorithm pages](#per-logic-algorithm-pages)
- [Boolean logic (shared syntax)](#boolean-logic-shared-syntax)
- [CTL (Computation Tree Logic)](#ctl---computation-tree-logic)
- [NatSL](#natsl---natural-strategy-logic)
- [OATL](#oatl)
- [OL](#ol)
- [RBATL / RABATL](#rbatl--rabatl)
- [CapATL](#capatl)
- [COTL](#cotl)
- [Wallet_ATL](#wallet_atl)
- [ICTL](#ictl---intuitionistic-ctl)
- [IATL](#iatl---intuitionistic-atl)
- [TCTL](#tctl---timed-ctl)
- [TOL](#tol---timed-obstruction-logic)
- [Empty and repeated coalition policy](#empty-coalition-policy)
- [Names and keywords](#names-and-keywords)
- [Syntax cards](#syntax-cards)
- [Logic comparison matrix](#summary-logic-comparison-matrix)
- [Model syntax](#model-syntax)
- [Technical references](#technical-references)

## Overview

The knowledge base holds:

- The syntax every logic shares: [connectives](#boolean-logic-shared-syntax),
  [Until after a prefix](#until-after-a-prefix),
  [a prefix before a connective](#prefix-before-a-connective) and
  [operators and names](#operators-and-names).
- One section for each of CTL, NatSL, OATL, OL, RBATL and RABATL, CapATL, COTL,
  Wallet_ATL, ICTL, IATL, TCTL and TOL: the syntax and semantics from the literature,
  the grammar and model type the code accepts, and for most of them a table that
  sets theory beside implementation. LTL, ATL, ATLF, ATL*, NatATL (with
  NatATL_Recall) and NatATLF have no section of their own; their algorithm pages
  below hold that material.
- The shared policies: [empty and repeated coalitions](#empty-coalition-policy),
  [names and keywords](#names-and-keywords), the [syntax cards](#syntax-cards) (one
  table row per logic with its prefix, operators, model type and an example), a
  [summary table](#summary-logic-comparison-matrix), and a
  [list of model types](#model-syntax).

## Per-logic algorithm pages

Each logic has its own algorithm page:

- [CTL](CTL/algorithm.md)
- [LTL](LTL/algorithm.md)
- [ATL](ATL/algorithm.md)
- [ATLF](ATLF/algorithm.md)
- [ATL*](ATL_STAR/algorithm.md)
- [NatATL](NatATL/algorithm.md)
- [NatATLF](NatATLF/algorithm.md)
- [NatSL](NatSL/algorithm.md)
- [OATL](OATL/algorithm.md)
- [OL](OL/algorithm.md)
- [RBATL](RBATL/algorithm.md)
- [RABATL](RABATL/algorithm.md)
- [CapATL](CapATL/algorithm.md)
- [COTL](COTL/algorithm.md)
- [Wallet_ATL](Wallet_ATL/algorithm.md)
- [ICTL](ICTL/algorithm.md)
- [IATL](IATL/algorithm.md)
- [TCTL](TCTL/algorithm.md)
- [TOL](TOL/algorithm.md)

<a id="boolean-logic-shared-syntax"></a>
## Boolean logic (shared syntax)

All logics in VITAMIN share a common set of boolean operators and constants. The
boolean constants are `true` and `false`. Table 1 lists the boolean operators,
ordered by precedence:

**Table 1: Boolean operators, ordered by precedence.**

| Operator | Syntax | Description |
| :--- | :--- | :--- |
| Negation | `!` | Logical NOT |
| Conjunction | `&&` | Logical AND |
| Disjunction | `\|\|` | Logical OR |
| Implication | `->` | Logical implication (p -> q) |

The word forms `not`, `and`, `or` and `implies`, and the logics that read them, are
in [word operators](#word-operators).

Every logic spells the connectives this way. A single `&` or `|`, and `>` as
implication, are rejected in all of them
(`model_checker/tests/unit/parsers/formulas/test_connective_spelling.py`), so a
formula is never valid in one logic and invalid in another. NatSL goals take no
connectives.

### Grouping and nesting

Table 2 lists the brackets that group a formula and the logics that take them:

**Table 2: Grouping and nesting brackets.**

| Syntax | Description | Supported logics |
| :--- | :--- | :--- |
| `(...)` | Standard grouping | All logics |
| `[...]` | Around the Until of a path quantifier, `A[p U q]` (CTL, ICTL), or its Release, `E[p R q]` (ICTL) | CTL and ICTL only |

CTL writes square brackets only around an Until, `A[f1 U f2]`, and groups
everything else with parentheses (Clarke, Emerson, Sistla, ACM TOPLAS 1986,
p. 246). ICTL writes them once, around a Release (EUMAS25b, Bozzelli et al., EUMAS 2025, p. 10), and ICTL
also takes them around an Until because its grammar treats U and R alike (see
[the ICTL reference](ICTL/algorithm.md)). `[p] && q` and `AF [p]` are syntax
errors, and so is `[...]` as grouping in every other logic (IATL writes `[1,2]` as a
coalition, see [IATL](#iatl---intuitionistic-atl)).

### Until after a prefix

A prefix is the part of a formula that scopes over what follows it: a coalition
(`<1>`, `<<1>>`), a coalition with a bound (`<1><5>`, the OL and TOL demonic
bounds `<J5>` and `{J2}`) or a CTL path quantifier (`A`), each with the temporal
operator after it (`<1>F`, `AF`), and the TCTL/TOL freeze `j.`. In every logic
with a prefix before Until, `prefix p U q` and `prefix (p U q)` are the same
formula and build the same tree: `<1> p U q` and `<1> (p U q)`, `<J5> p U q` and
`<J5> (p U q)`, `A p U q` and `A(p U q)`. ATL writes the first form (Alur,
Henzinger, Kupferman, JACM 2002, p. 685), and the obstruction logics write the
second. ATL* reads `<<A>> p U q` the same way; the reason and the other ATL* forms
are in [the ATL* reference](ATL_STAR/algorithm.md). Release (`R`) and Weak Until
(`W`) follow the same rule where a logic has them. The 17 logics covered are listed
in `model_checker/tests/unit/parsers/formulas/test_until_after_prefix.py`.

### Prefix before a connective

When no parenthesis closes a prefix, a connective after it has two readings:
`<1>F p && q` is `(<1>F p) && q` or `<1>F (p && q)`, and `<1> p U q && r` is
`(<1> (p U q)) && r` or `<1> (p U (q && r))`. No defining paper states which, so in
every logic with a prefix this is a syntax error that gives the position and both
readings, for `&&`, `||` and `->` in any spelling (`and`, `or`, `implies`):

```text
'<1>F ... && ...' is ambiguous: write <1>F (... && ...) for <1>F over both sides,
or (<1>F ...) && ... for <1>F over the left side only (position 0)
```

The same holds after a negation (`!<1>F p && q`), after a connective
(`q && <1>F p && r`) and after a TCTL/TOL clock constraint (`AF p : x<5 && q`).
These parse, because they have one reading:

- A prefix at the end: `q && <1>F p`.
- A prefix closed by parentheses: `(<1>F p) && q`, `<1>F (p && q)`,
  `<1> (p U q) && r`.
- A connective in the left operand of a prefix Until: `<1> p && q U r` is
  `<1> ((p && q) U r)`, because `<1> p` alone is no formula of these logics.

ATL* differs, because `<<1>> p` and a bare Until inside a coalition are ATL*
formulas; its rules and messages are in [the ATL* reference](ATL_STAR/algorithm.md).
LTL has no prefix: its `F`, `G`, `X` and `U` follow the precedence table of the
[Spot LTL library](https://spot.lre.epita.fr/tl.pdf) (section 3.1), so
`F p && q` is `(F p) && q` and `p U q && r` is `(p U q) && r`.
NatSL has no connectives after its prefix, so it rejects `E{1}x: (x, 1) F p && q`
without offering two readings; see [the NatSL reference](NatSL/algorithm.md#supported-fragment).

### Operators and names

Temporal operators (`X`, `F`, `G`, `U`, and in CTL and ICTL `AX`, `AF`, `AG`, `EX`, `EF`, `EG`) are words of their own. TCTL has no `X` (see [the TCTL reference](TCTL/algorithm.md)).
Follow one with a space, `(` or `!`: `F p`, `F (p && q)`, `F !p`.

A name starts with a lowercase letter ([names and keywords](#names-and-keywords)), so an operator glued to a name, such as `Fp`, is an error; the three ways it fails are in [operators glued to a name](#operators-glued-to-a-name).
A binary operator follows the same rule: `pUq` starts lowercase, so it is one name like any other and must be declared in the model; `p U q` is the Until.

Every logic follows this rule, and `model_checker/tests/unit/parsers/formulas/test_operator_spacing.py` checks it for each registered logic.

A name the model does not declare is an error in every logic, wherever it sits in the formula: under `!`, inside an Until or a conjunction.
The error type is `semantic` (NatSL reports `validation`), so a typo never reads as a proposition that is false everywhere, which would make `AG !typo` true.
The message names it: "Proposition(s) 'zz' not among the model's declared propositions [...]"; NatSL words it "Unknown proposition 'zz'; model propositions are [...]".
`model_checker/tests/integration/algorithms/test_error_contract.py` checks this for each registered logic.

The truth table of the boolean operators:

```text
   p   |   q   |  !p   | p && q | p || q | p -> q
-------|-------|-------|--------|--------|--------
 true  | true  | false |  true  |  true  |  true
 true  | false | false |  false |  true  |  false
 false | true  | true  |  false |  true  |  true
 false | false | true  |  false |  false |  true
```

<a id="ctl---computation-tree-logic"></a>
## CTL (Computation Tree Logic)

### Theoretical background

CTL is a branching-time logic defined over computation trees. Formulas are evaluated at a state and quantify over all possible infinite paths from that state.

#### Standard syntax

- Path quantifiers:
    - `E`: there exists a path...
    - `A`: for all paths...
- Temporal operators:
    - `X`: next state
    - `F`: eventually (finally)
    - `G`: globally (always)
    - `U`: until

#### Standard examples

- `AG p`: always globally p (p is an invariant).
- `EF p`: eventually p (reachability).
- `AG (p -> AF q)`: always if p, then eventually q on all paths (liveness/response).

#### Traces (optional)

With `generate_trace=True` the result has a `trace` for
the outermost operator of the formula at the initial state: a witness when an
operator that starts with `E` holds, a counterexample when one that starts with
`A` fails, and `None` otherwise. See [Traces](CTL/algorithm.md#traces) for each
case.

### Implementation

The parser is `model_checker/parsers/formulas/CTL/parser.py` and the algorithm is
in `model_checker/algorithms/explicit/CTL/`. The implementation supports:

- Path quantifiers `E` / `A` with temporal operators `X`, `F`, `G`, and `U`.
- Boolean connectives shared with the common formula syntax.
- Optional traces (`generate_trace=True`): a witness or a counterexample for the
  outermost operator, as described under [Traces (optional)](#traces-optional) above.

See [CTL algorithm reference](CTL/algorithm.md) for denotations and operators.

<a id="natsl---natural-strategy-logic"></a>
## NatSL (Natural Strategy Logic)

### Theoretical background

NatSL quantifies over bounded natural strategies and binds those strategies to
agents. The checker implements a restricted one-goal fragment.

#### Standard syntax

- Existential / universal strategy quantifiers with complexity bounds: `E{k}x`,
  `A{k}y`.
- Explicit agent bindings: `(x, 1)(y, 2)`.
- Temporal goals: `F`, `G`, `X`, and their negations.

A representative formula is:

```text
E{2}controller A{1}opponent: (controller, 1)(opponent, 2) F goal
```

### Implementation

The parser is `model_checker/parsers/formulas/NatSL/parser.py` and the algorithm is
`model_checker/algorithms/explicit/NatSL/core.py`. The implementation supports:

- Ordered prefixes of the form `E* A*`, including purely existential prefixes. The
  parser also accepts other orders (`A{1}x E{1}y:`); `model_checking` then returns
  a validation error that asks for an `E* A*` prefix.
- Multi-character strategy variables and explicit agent bindings. The bindings cover
  every agent of the model exactly once, so `E{1}x: (x, 1) F goal` checks only on a
  1-agent model.
- A goal is an operator, a space and a proposition (`F goal`); see [operators and names](#operators-and-names).
- Exact action pruning (no idle-action fallback).
- Direct evaluation of mixed bounded prefixes (no NatATL decomposition).

### Execution schedules

Both schedules share the same acceptance semantics:

- `mode="space"`: space-oriented lazy search.
- `mode="time"`: time-oriented materialized search.

`model_checking` uses `space` when no mode is given. See [NatSL algorithm](NatSL/algorithm.md) and [NatSL semantics](NatSL/semantics.md).

<a id="oatl"></a>
## OATL

### Theoretical background

OATL (Obstruction Alternating-time Temporal Logic) is defined in D. Catta,
J. Leneutre, V. Malvone, A. Murano, "Obstruction Alternating-time Temporal
Logic: a Strategic Logic to Reason about Dynamic Models", AAMAS 2024. Besides
the agents of a [`costCGS`](file_formats.md#costcgs-sections), a single extra
player, the Demon, can temporarily erase transitions. Erasing joint action `a` at
state `s` costs `$(s, a)`.

#### Standard syntax

- Bounded coalition: `[[A]]_n theta` in the paper, `<A><n> theta` in VITAMIN
    - `A`: the coalition of agents.
    - `n`: the Demon's budget per step.
- Operators: `X`, `U`, `R` are primitive; `F`, `G`, `W` are derived.

#### Semantics

- `<A><n> theta` holds at `s` when the Demon has a strategy that, at each step,
  erases a set of joint actions of total cost at most `n` (never all of them),
  such that for every strategy of `A`, some remaining path satisfies `theta`.
  The agents outside `A` resolve the remaining choices in the Demon's favour.
- The budget applies to each step separately; it is not a sum along the path.
- Example: on the Figure 1 model of the paper
  (`model_checker/tests/fixtures/costCGS/OATL/oatl_3agents_medium_6states_costs.txt`),
  `<1,2><2> G !(r && s && g)` is false at `s0` and `<1,2><3> G !(r && s && g)`
  is true. The least budget that stops the attack is 3, as the paper states.

### Implementation

The parser is `model_checker/parsers/formulas/OATL/parser.py`.

#### Supported syntax

- Format: `<coalition><budget>` (e.g., `<1,2><10>`), with no space between
  the two parts (`<1> <5>` is an error).
- Temporal operators: `X`, `F`, `G`, `U`, `R`, `W` (and their keywords).
- Propositions: `[a-z][a-zA-Z0-9_]*` (see [names and keywords](#names-and-keywords)).
- Boolean constants: `true` and `false`.

#### Validation rules

- Budget requirement: a budget is mandatory for every coalition-prefixed temporal operator.
- Budget value: the budget `n` is an integer `n >= 0` with no leading zeros. With `n = 0` the Demon can erase only zero-cost joint actions.
- Parentheses: binary operators may be written as in the paper, `<A><n> (phi U psi)`, or without parentheses.

#### Costs

Each `Costs_for_actions` entry gives the Demon's cost to erase that
joint action at that state. A cost vector (`1:2:0`) is summed into one cost.
A transition may have no cost; the check fails, naming the states and actions,
only when the result depends on those missing costs.

#### Formula examples

```text
<1><5> F goal
<1,2><10> (safe W unsafe)
<1,2><3> (false R !(r && s && g))
<1><0> X p
```

### Theory and implementation

Table 3 sets the paper beside the code:

**Table 3: OATL, theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Coalition | `[[A]]` | `<1,2>` (indices) |
| Budget | `n` in N, per step | `<n>` with `n >= 0`, per step |
| Temporal ops | X, U, R (F, G, W derived) | `X`, `F`, `G`, `U`, `R`, `W` |
| Algorithm | Proposition 1 and Theorem 1 | `OATL/preimage.py` and fixpoints in `OATL/operators.py` |

<a id="ol"></a>
## OL

### Theoretical background

OL (Obstruction Logic, ECAI 2023) is a game against a Demon on `costCGS` models: `<Jk> phi` holds when the Demon, with a budget of `k` at each step, can disable edges so that every remaining path satisfies `phi`.
It is OATL with the coalition of all agents.
The [OL algorithm reference](OL/algorithm.md) gives the rules and the sources.

The standard syntax is the cost prefix `<Jk> phi`, where `k` is a natural number, 0 included.

### Implementation

The parser is `model_checker/parsers/formulas/OL/parser.py`.

#### Supported syntax

- Format: `<Jk>` (e.g., `<J5>`). The letter `J` is mandatory inside the angle brackets.
- Temporal operators: `X`, `F`, `G`, `U`, `R`, `W`.
- Propositions: `[a-z][a-zA-Z0-9_]*` (see [names and keywords](#names-and-keywords)).

#### Validation rules

- Mandatory `J`: OL prefixes must use `<Jk>`, not bare `<k>`.
- Bound requirement: every temporal operator must be prefixed with `<Jk>`.
- Bound: `k >= 0` with no leading zero; `<J0>` is valid and `<J01>` is rejected.

#### Formula examples

```text
<J5> F goal
<J10> G ok
<J3> (p U q)
```

### Theory and implementation

Table 4 sets the paper beside the code:

**Table 4: OL, theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Cost prefix | `<Jk>` | `<Jk>` (requires `J`) |
| Temporal ops | X, F, G, U | X, F, G, U, R, W |
| Cost semantics | Demon budget `k` at each step | Same, through the OATL operators with the coalition of all agents |

<a id="rbatl--rabatl"></a>
## RBATL / RABATL

### Theoretical background

RBATL and RABATL extend ATL with vector cost bounds on coalition strategies over `costCGS` models.

The standard syntax is the vector bounded coalition `<A><b1, b2, ...> phi`:

- `A`: coalition agents.
- `b1, b2, ...`: per-resource bounds.

### Implementation

The parsers are `RBATL/parser.py` and `RABATL/parser.py`, with the same surface syntax.

#### Supported syntax

- Format: `<coalition><bound1,bound2,...>` (e.g., `<1><10,5>`), with no space
  between the two parts (`<1> <5>` is an error).
- Temporal operators: `X`, `F`, `G`, `U` (`R`/`W` rejected at parser).
- Multi-resource bounds: comma-separated inside the second angle-bracket group.

#### Validation rules

- Comma separation: resource vectors use commas, not colons.
- Bound range: each bound value is between 1 and 1,000,000. `<1><0,5>F p` is an error, "Invalid bound value 0: must be between 1 and 1000000".
- Resource count: the length of the bound vector is not checked against the model. Bound `i` limits cost value `i`; cost values beyond the last bound are not limited, and bounds beyond the last cost value are ignored (`RBATL/preimage.py`, `RABATL/preimage.py`).

#### Cost models

- RBATL uses flat `Costs_for_actions` entries (one line per joint action, `action state$cost[:cost...]`, see [costCGS sections](file_formats.md#costcgs-sections)).
- RABATL uses `Costs_for_actions_split` and sums coalition members' cost components when checking a joint action.

#### Semantics

In both logics, on each coalition-controlled transition, resource `i` consumed must satisfy `cost_i <= b_i` for each bound `b_i` given (per-step affordability, not cumulative path totals).

#### Formula examples

```text
<1><100,50> F goal
<1,2><10,10,10> G safe
<1><5> (p U q)
```

### Theory and implementation

Table 5 sets the paper beside the code:

**Table 5: RBATL and RABATL, theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Coalition | `<A>` | `<1,2>` (indices) |
| Vector bound | `<b1, b2, ...>` | `<10,5>` (comma-separated) |
| Temporal ops | X, F, G, U | `X`, `F`, `G`, `U` (R/W rejected at parser) |
| RBATL costs | Flat action costs | `Costs_for_actions` |
| RABATL costs | Split / coalition-sum | `Costs_for_actions_split` |

RABATL is not a separate recursive-modality engine in VITAMIN. It shares `bounded_atl_solver` with RBATL and differs only in how action costs are derived from the model file.
Winning sets can differ from RBATL on the same formula when coalition-sum costs disagree with flat costs.

Release (`R`) and Weak Until (`W`) are rejected at parse time for RBATL/RABATL.

<a id="capatl"></a>
## CapATL

### Theoretical background

CapATL is designed for models with explicit capacity constraints ([`capCGS`](file_formats.md#capcgs-sections)), often involving knowledge (capability) and agent-scoped properties.

#### Standard syntax

- Coalition modality: `<{A}> phi` (paper-style agent set; capacities constrain
  available actions via the `capCGS` model, not a formula numeric bound).
- Knowledge: K^a_cap(phi) (AAMAS 2024, grammar p. 125, meaning p. 126),
  "agent a knows that the capacity assignment verifies phi", where phi is a
  capacity assignment formula built from `a -> c` (agent `a` has capacity `c`),
  negation and conjunction.

### Implementation

The parser is `model_checker/parsers/formulas/CapATL/parser.py`.

#### Supported syntax

- Coalition: `<{agent1,agent2,...}>` (curly braces required; no `, k`).
- Knowledge: `K1(2 is c)`, `K2(!(3 is c) && 1 is cop)`, alias `kcap1(...)`,
  where `a is c` is the paper's `a -> c`. Accepted forms, errors and precedence
  are in [the CapATL reference](CapATL/algorithm.md#formula-language).
- Temporal operators: `X`, `F`, `G`, `U`, and binary `R` (Release).

#### Validation rules

- Model requirement: can only be verified against `capCGS` models.
- Formula bound: `<{A}, k>` is rejected (no numeric `k` in CapATL).
- Weak Until: `W` is not part of CapATL path syntax and is unsupported.
- Release: `R` is accepted as a binary operator (`<{A}> phi R psi`) and evaluated by the CapATL solver (greatest fixpoint).

#### Formula examples

```text
<{1,2}> F g
<{1}> G a
<{1,2,3}> X a
<{1}> a R g
<{1}> false R g
```

### Theory and implementation

Table 6 sets the paper beside the code:

**Table 6: CapATL, theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Coalition | `<A>` / `<{A}>` | `<{A}>` (braces required; no formula `k`) |
| Capacities | Model / knowledge | `capCGS` sections + Pre over capacity knowledge |
| Knowledge | K^a_cap(phi) | Parsed as `K1(...)`, the digit being the agent number; model checking returns a validation error that names the operator |
| Temporal | X, U, R (F/G sugar) | `X, F, G, U, R` (`W` unsupported) |

<a id="cotl"></a>
## COTL

### Theoretical background

COTL (Coalition Obstruction Temporal Logic) is defined in D. Catta, J. Leneutre,
V. Malvone, A. Murano, "Coalition Obstruction Temporal Logic: A New Obstruction
Logic to Reason About Demon Coalitions", IJCAI 2025. It runs on an
[`ObstructionModel`](file_formats.md#obstructionmodel-sections-cotl): a graph of states, with no agents, whose edges several
demons can temporarily disable. Each demon action has a cost, and the idle
action `*` costs 0. The attacker is the path itself.

#### Standard syntax

- Legion modality: `<<G>>_n theta` in the paper, `<G><n> theta` in VITAMIN
    - `G`: a set of demons (a legion), possibly empty.
    - `n`: the legion's budget per step, `n >= 0`.
- Operators: `X`, `X~` (weak next), `U`, `R` are primitive; `F`, `G`, `W` are derived.

#### Semantics

`<G><n> theta` holds when the legion has a strategy that, at
each step, picks one action per member of total cost at most `n`, such that
every path left by the disabled edges satisfies `theta`, whatever the other
demons do. A path may stop when every edge out of its last state is disabled.
Example: on the case-study attack graph of the paper
(`model_checker/tests/fixtures/ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt`),
`<1,3><1> G !q` holds at `s0` and `<1,2><1> G !q` does not, as Sec. 5 states.

### Implementation

The parser is `COTLParser` (`model_checker/parsers/formulas/COTL/parser.py`).

#### Supported syntax

- Format: `<legion><budget>` (e.g., `<1,3><1>`, `<><0>`). Demon indices go from 1 to `Number_of_demons`.
- Temporal operators: `X`, `WX` (weak next), `F`, `G`, `U`, `R`, `W`. Binary operators may be written `<G><n> (phi U psi)` or without parentheses.
- Propositions: `[a-z][a-zA-Z0-9_]*` (see [names and keywords](#names-and-keywords)).

#### Formula examples

```text
<1,3><1> G !q
<1><2> WX safe
<><0> X p
<1,2><3> (p U q)
```

### Theory and implementation

Table 7 sets the paper beside the code:

**Table 7: COTL, theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Legion | `<<G>>`, any subset of demons | `<1,3>`, `<>` for the empty legion |
| Budget | `n` in N, per step | `<n>` with `n >= 0`, per step |
| Weak next | `X~` | `WX` |
| Paths that stop | Allowed | `G`, `R`, `W`, `WX` hold on them; `X`, `U`, `F` need a next state |

COTL and OATL both come from obstruction logic, but they share no checker
code. In OATL a single Demon helps against a coalition of agents on a
`costCGS` (see [OATL](#oatl)). In COTL a legion of demons acts against the
other demons and the path, on an `ObstructionModel`.

<a id="wallet_atl"></a>
## Wallet_ATL

ATL with wallet-aware coalitions over [`WalletCGS`](file_formats.md#walletcgs-sections) models.

The coalition syntax is `<<agents[:wallet constraints]>>` followed by a temporal formula.
The `<<>>` prefix is mandatory before `X`, `F`, `G`, or `U`; bare temporal operators without a coalition are rejected.
Each wallet guard names a coalition agent, and every guard must hold; see [Wallet_ATL formula language](Wallet_ATL/algorithm.md#formula-language).

Wallet_ATL uses a `<<...>>` prefix instead of `<1>` because plain ATL uses `<1>` for
coalitions only, while Wallet_ATL embeds optional balance guards (`:wallet(agent, op value)`)
inside the same prefix, so the grammar uses a dedicated `<< ... >>` token. That
avoids clashing with other bracket conventions in VITAMIN: OATL/RBATL `<1><5>`
(coalition then cost bound), NatATL `<{1}, k>`, CapATL `<{1}>`, and OL `<Jk>`.
OATL's two bracket groups are separate tokens; Wallet's double brackets are one
nested delimiter around agents plus guards.

For example:

```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50)>>G funded
```

The temporal operators are `X`, `F`, `G`, `U`. The model type is `WalletCGS`. See [Wallet_ATL usage](Wallet_ATL/usage.md).

A wallet guard is checked against the balances in the `Wallets`
section at the state where a coalition move starts. Balances are not
recomputed along transitions. Where each operator checks the guard is in
[Wallet_ATL operators](Wallet_ATL/algorithm.md#operators).

A joint move is available only when every agent can pay for its part, so a
`D20` move needs at least 20 in the acting agent's wallet. The rules are in
[Wallet_ATL algorithm](Wallet_ATL/algorithm.md#semantic-denotations).

<a id="ictl---intuitionistic-ctl"></a>
## ICTL (Intuitionistic CTL)

### Theoretical background

ICTL (Intuitionistic CTL) extends CTL with intuitionistic propositional
connectives over [birelational models](file_formats.md#birelationalmatrix-sections-ictl) (EUMAS25b). Each
model has two relations on the same finite state set:

- `P` (`<=_P`): information preorder; truth is monotone as knowledge grows.
- `R`: serial transition relation; path quantifiers range over infinite `R`-paths.

Path formulas (`X`, `U`, `R`) use standard CTL semantics on `R`-paths. Only
implication and negation are intuitionistic: `phi -> psi` is checked at all
`P`-refinements of the current state.

The paper's well-behaved frames satisfy the confluence constraints C1 and C2
between `P` and `R` (EUMAS25b Def. 1). See [ICTL/algorithm.md](ICTL/algorithm.md).

#### Standard syntax (state formulas)

- Boolean: `->`, `not`, `/\`, `\/` (implication is primitive; no excluded middle).
- Path quantifiers: `E`, `A` over `R`-paths.
- Temporal: `X`, `U`, `R`; surface sugar `F` / `G` after `E` or `A`.

#### Sugar encodings (EUMAS25b fixpoints)

- `EF phi` = `E(T U phi)`
- `EG phi` = `E(bottom R phi)`
- `AF phi` = `A(T U phi)`
- `AG phi` = `A(bottom R phi)`

Classical CTL complement dualities (for example `AF phi` as `S \ EG(~phi)`) are
not valid in ICTL and are not used by the checker.

### Implementation

The parser is `model_checker/parsers/formulas/ICTL/parser.py` (`ICTLParser`) and
the checker is in `model_checker/algorithms/explicit/ICTL/`.

The model loader is `parsers/game_structures/birelational_matrix/`
(`BirelationalMatrix`, a `CGS` subclass). Cell labels: `0`, `R`, `P`, `P,R`.
Diagonal cells should be `P` or `P,R` so reflexivity of `P` holds. Metadata:
`model_type: "BirelationalMatrix"`.

#### Supported syntax

- Quantifiers: `E` / `exist`, `A` / `forall`.
- Temporal: `X`, `U`, `R`; sugar `F` / `G` (also `eventually`, `globally`, etc.).
- Boolean: `&&`, `||`, `!` / `not`, `->` / `implies`.
- Propositions: `[a-z][a-zA-Z0-9_]*` ([names and keywords](#names-and-keywords)). Path/temporal
  tokens (`E`, `A`, `X`, `F`, `G`, `U`, `R`, keywords) are lexed separately so
  forms such as `EX` / `AG` are operators, not atoms.

#### How each operator is checked (set-based model checking)

- `phi -> psi`, `not phi`: upward closure (`^up`) along `P`.
- `EX phi`: `Pre_exists([[phi]])`; `AX phi`: `Pre_forall([[phi]])` (no `^up` on `AX`).
- `EU` / `AU` / `ER` / `AR`: least / greatest fixpoints per EUMAS25b Theorem 3.
- `EF` / `EG` / `AF` / `AG`: direct fixpoint encodings above (not complement tricks).

#### Formula examples

```text
EX e
EF e
AX e
AF e
AG (p -> EF q)
AG goal
E p R q
!(e -> h)
```

The model type is `BirelationalMatrix`. The algorithm, C1/C2 validation and
denotations are in [ICTL/algorithm.md](ICTL/algorithm.md).

### Theory and implementation

Table 8 sets the paper beside the code:

**Table 8: ICTL, theory (EUMAS25b) and implementation.**

| Aspect | Theory (EUMAS25b) | Implementation |
| :--- | :--- | :--- |
| Model | Birelational frame + monotone valuation | `BirelationalMatrix` + `check_conditions_hold` |
| Frame constraints | C1, C2 (well-behaved) | C1, C2 (EUMAS25b Def. 1); no paper C3 |
| `->`, `not` | Intuitionistic (`^up`) | `handle_implies`, `handle_not` with `^up` |
| `AX` | `Pre_forall([[phi]])` | `handle_ax` = `Pre_forall` (no `^up`) |
| `AF` / `AG` | `A(T U phi)` / `A(bottom R phi)` | `handle_af` / `handle_ag` (direct fixpoints) |
| `EF` / `EG` / `EU` / `AU` / `ER` / `AR` | Standard fixpoints on `R` | Same as paper Figure 7 |
| Complexity | `O(\|M\|^2 * \|phi\|)` PTIME | Explicit set-based checker |

<a id="iatl---intuitionistic-atl"></a>
## IATL (Intuitionistic ATL)

### Theoretical background

IATL (Intuitionistic ATL) extends ATL with intuitionistic propositional
connectives and dual coalition modalities over [BCGS](file_formats.md#bcgs-sections-iatl) models (Bozzelli et al.,
KR 2025). Each model combines:

- CGS transitions: joint action profiles (multi-agent moves).
- Preorder `P`: information refinement; intuitionistic truth is monotone along `P`.

The coalition modalities are written `<A>` and `[A]` for the paper's `<<A>>` and
`[[A]]`:

- `<A> phi`: coalition `A` has a strategy enforcing `phi`.
- `[A] phi`: no strategy of `A` can prevent `phi`.

In the paper (Definition 2), a well-behaved BCGS satisfies the per-coalition
constraints C1 and C2 (contravariant simulation of coalition decisions along `P`).

#### Sugar encodings (KR 2025 fixpoints)

- `<A> F phi` = `<A>(T U phi)`; `[A] F phi` = `[A](T U phi)`
- `<A> G phi` = `<A>(bottom R phi)`; `[A] G phi` = `[A](bottom R phi)`

On finitely-branching BCGS, perfect-recall and memoryless semantics coincide
(Theorem 5); the explicit checker uses memoryless coalition pre-images.

### Implementation

The parser is `model_checker/parsers/formulas/IATL/parser.py` and the checker is in
`model_checker/algorithms/explicit/IATL/`.

The model loader is `parsers/game_structures/bcgs/` (`BCGS`, a `CGS` subclass).
Files use CGS `Transition` cells (joint actions) plus a boolean `Preorder`
section. Metadata: `model_type: "BCGS"`.

#### Coalition pre-images (Proposition 2)

- `Pre_d(A, X)` (`pre_exists`): some `A`-decision; all opponent responses stay in `X`.
- `Pre_f(A, X)` (`pre_forall`): every `A`-decision; some response lands in `X`.

#### How each operator is checked

- `phi -> psi`, `! phi`: upward closure (`^up`) along `P`.
- `<A> X phi`: `Pre_d`; `[A] X phi`: `Pre_f` (no `^up` on `[A] X`).
- `U` / `R` / `F` / `G`: fixpoints per Theorem 4 (Figure 4).

#### Formula examples

```text
<1>G a
[1,2]F goal
<1,2> p U safe
<1>X p
[1]X p
!p
p -> q
```

The model type is `BCGS` with separate `Preorder` section. See
[IATL/algorithm.md](IATL/algorithm.md) for validation, denotations, and pipeline.

### Theory and implementation

Table 9 sets the paper beside the code:

**Table 9: IATL, theory (KR 2025) and implementation.**

| Aspect | Theory (KR 2025) | Implementation |
| :--- | :--- | :--- |
| Model | BCGS + monotone valuation | `BCGS` + `check_conditions_hold` |
| Frame constraints | C1, C2 per coalition | `_check_well_behaved_c1/c2` |
| `->`, `!` | Intuitionistic (`^up`) | `handle_implies`, `handle_not` |
| `[A] X` | `Pre_f(A, [[phi]])` | `handle_coalition_next_forall` = `Pre_f` |
| `<A> X` | `Pre_d(A, [[phi]])` | `handle_coalition_next_exists` |
| `F` / `G` | `U` / `R` encodings above | Direct fixpoint handlers |
| Strategies | Perfect recall = memoryless (finitely branching) | State-based pre-images |
| Complexity | `O(\|G\|^2 * \|phi\|)` PTIME | Explicit set-based checker |

<a id="tctl---timed-ctl"></a>
## TCTL

Timed CTL over [`timedCGS`](file_formats.md#timedcgs-sections) models. Checking uses a zone graph as the symbolic RTS
and the `rsat` regional labelling algorithm.

The quantifiers are `A` and `E`, with `F`, `G`, `U` (no `X` or release).

Clocks and clock guards:

- Automaton clocks `X` from the model `Clocks` section.
- Formula clocks `Y` via freeze `j.phi` (reset `j` to `0`, paper `j.reset(phi)`).
- Guards: standalone `x <= 5` or attachment `phi : x <= c` on subformulas.

For example:

```text
AG a
EF crossing
EF (p : x<=1)
j.A(j<=7 U goal)
```

The model type is `timedCGS` (`TimedCGS.read_file`). The
[TCTL algorithm reference](TCTL/algorithm.md) has the details.

<a id="tol---timed-obstruction-logic"></a>
## TOL

Linear-style Timed Obstruction Logic with demonic cost prefixes over `timedCGS`
models (AAMAS 2025). At each step the Demon may deactivate outgoing transitions
whose total cost is at most `k`; the Adversary chooses a remaining edge.

The demonic prefix is `{Jk}`, where `k` is a positive integer (paper notation `<k>`).
For example:

```text
{J5}F a
{J10}G safe
{J3}(p U q)
j.{J5}(j<=7 U goal)
```

The temporal operators are `F`, `G`, `U`, `R`, `W` (paper) and `X` (VITAMIN extension).

The cost `k` is a per-position demonic deactivation budget (paper
obstruction game), not cumulative path cost. OL (`<Jk>`) reads its budget the
same way.

The freeze `j.phi` resets formula clock `j` to `0` at the current state.

The model type is `timedCGS`, and TOL shares the `timed_cgs` parser with TCTL. The
[TOL algorithm reference](TOL/algorithm.md) has the details.

<a id="empty-coalition-policy"></a>
## Empty and repeated coalition policy

Outside COTL, VITAMIN does not support an empty strategic coalition written as `<>`.
In ATL literature an empty coalition can be related to opponent-only or path-level reasoning; in this implementation that overlaps CTL existential quantification (`E`, `EF`, ...) without making the logic explicit.

The policy is to reject `<> ...` in every logic except COTL, whose legion of demons may be empty (`<><0>`). Table 10 gives the correct surface for each property:

**Table 10: Surface to use for each property.**

| Intent | Use | Do not use |
| :--- | :--- | :--- |
| Existential path reachability (CTL) | `EF p` | `<> F p` |
| Strategic coalition (ATL) | `<1> F p`, `<1,2> G p` | `<> F p` |
| Linear path eventually (LTL) | `F p` | `<> F p` |
| Cost-bounded strategy (OATL / RBATL) | `<1><5> F p` | `<> F p`, `<1> F p` without bound, `<1> <5> F p` |
| Capacity / strategy-bound (NatATL) | `<{1}, 5> F p` | `<> F p` |
| Capacity coalition (CapATL) | `<{1}> F p` | `<> F p` |
| IATL universal coalition | `[1] G p` | `[] G p` (empty `[]` rejected) |

Table 11 lists where the rejection is enforced, for the logics whose coalition form
differs; ATL*, NatATL_Recall, NatATLF, TCTL and TOL are not listed:

**Table 11: Where an empty coalition is rejected.**

| Logic | Coalition form | Empty coalition |
| :--- | :--- | :--- |
| ATL / ATLF | `<1>`, `<1,2>` | `<> ` rejected (precheck + parser) |
| IATL | `<1>` exist, `[1]` forall | `<> ` and `[]` rejected |
| NatATL | `<{1,2}, k>` | `<\s*>` rejected |
| CapATL | `<{1,2}>` | `<\s*>` rejected |
| OATL | `<1><5>` | `<\s*>` rejected; bound required |
| COTL | `<1,3><1>` | `<><0>` allowed (empty legion of demons); bound required |
| RBATL / RABATL | `<1><5>` or `<1><2,2>` | `<\s*>` rejected; bound required |
| OL | `<J5>` (cost, not agents) | N/A |
| Wallet_ATL | `<<1>>` | `<<>>` invalid (lexer) |
| CTL / LTL | `E` / `A` or none | `<> ` invalid syntax |

VITAMIN also rejects a coalition that lists an agent twice, because a coalition is a set of agents (ATL, JACM 2002 p. 685, rule S3: A "is a set of players").
This holds in every logic whose coalition lists agents, including IATL's `[A]` and COTL's list of demons (its legion).
For example, `<1,1> F p` in ATL and `<{2,1,2}> F p` in CapATL are errors that name the repeated agent.

<a id="names-and-keywords"></a>
## Names and keywords

This section is the one source for how names, reserved words and operator words
are written, in models and in formulas of every logic. Other docs link here.
Five rules cover it:

1. A name (proposition, clock, capacity) is `[a-z][a-zA-Z0-9_]*`, the same in
   models and formulas: `goal` and `goalA` are names, `P`, `Goal` and `GOAL` are
   errors (IATL, TCTL and TOL report `P` and `GOAL` as `Invalid character`).
2. The 17 [reserved words](#reserved-words) are never names, in any letter case.
3. A word operator such as `until` is an operator only in lowercase, and only in a
   logic that has the operator ([word operators](#word-operators)).
4. `true` and `false` are constants in lowercase only, in every logic.
5. Operator symbols (`F`, `U`, `AG`, and CapATL's knowledge operator `K1`, whose
   word form is `kcap1`) are uppercase only. With rule 1, a word that starts with an uppercase letter is
   never a name.

So each word has one reading. `p until q` is an Until. `p Until q` is an error,
because the parser meets `Until` where an operator must stand. `F Until` is an
error from the [reserved-word](#reserved-words) check, because `Until` stands where
a name must stand. `F Goal` gives "Atomic proposition 'Goal' is invalid", never a
proposition that is false everywhere.

### Names

Proposition, clock and capacity names follow rule 1 in a model and in a formula.
CGS action names (`A`, `block_a1`) and agent labels are not names in this sense and
may start with a capital.

- Pattern: `NAME_RE` in `model_checker/parsers/syntax_patterns.py`, a lowercase
  letter, then letters, digits or `_`.
- Formulas: `validate_proposition_identifier()` in
  `model_checker/parsers/formulas/parser_utils.py` checks, in every logic, the
  propositions of a formula, the capacity names of a CapATL formula and the clock
  names of a TCTL or TOL formula (in a freeze `x.phi` and a comparison `x<=2`).
- Models: `validate_model_name()` in
  `model_checker/parsers/game_structures/cgs/cgs_utils.py` applies the same check
  to the propositions of a CGS model, the `Clocks` section of a timedCGS model and
  the `Capacities` section of a capCGS model. So a model cannot declare a clock or
  capacity such as `Next` that no formula can name.

The message starts with the kind of name (`Atomic proposition`, `Clock` or
`Capacity`) and the word:

```text
Atomic proposition 'Goal' is invalid: a name starts with a lowercase letter, then letters, digits or _ ([a-z][a-zA-Z0-9_]*).
Atomic proposition 'Until' clashes with reserved keyword.
```

IATL, TCTL and TOL report an all-capital word such as `P` or `GOAL` as
`Invalid character` instead (see [lexer word patterns](#lexer-word-patterns)).

### Reserved words

Reserved words (any letter case): `and`, `or`, `not`, `implies`, `until`, `release`, `globally`, `next`, `eventually`, `always`, `forall`, `exist`, `weak`, `with`, `is`, `true`, `false`.

The list is `FORMULA_RESERVED_WORDS` in `syntax_patterns.py`: every operator word of
the [word operators](#word-operators) table plus the two constants. A word is
reserved in every logic, even where the logic has no such operator (`weak` in ATL,
`with` outside TOL), so a name means the same in every logic, apart from `kcap` below.

`kcap` (in any letter case) is reserved in CapATL only: in its formulas and in a
capCGS model (the only model type CapATL reads), as a proposition or a capacity name. CapATL writes its knowledge
operator `K1(...)` or `kcap1(...)`, and its parser reads `kcap` followed by digits
as that operator, so the bare word is the only spelling left to reserve. A capCGS
model also refuses names of `kcap` and digits (`kcap1`, `kcap42`), since no CapATL
formula could name them; `kcap1x` is an ordinary name. In the other logics and
plain CGS models `kcap` and `kcap1` stay valid names.

`true` and `false` are the boolean constants, so a model that declares a proposition, clock or
capacity with either name (`true`, `True`, `FALSE`, ...) is rejected when it is read. In a
formula they are constants in lowercase, and `True` is a reserved-word error.

### Word operators

Most operators have a word form beside the symbol: `p until q` is `p U q`, with the
same precedence. Table 12 lists every word, the symbol it stands for and the
logics that read it. The words are `OPERATOR_WORDS` in `syntax_patterns.py`, which
feeds every parser except NatSL's (its goal pattern reads `not` only), so a word is
spelled the same in every logic that has it. In a logic that does not read a word,
or in another letter case ([rule 3](#names-and-keywords)), the word is an error. `p Until q` gives
"Syntax error near token 'Until'" in every logic except two: ATL* gives the
reserved-word message and NatSL "Unsupported goal". CapATL's `kcap1(...)` is not in
the table, because the word carries the agent number; see `kcap` under
[reserved words](#reserved-words).

**Table 12: Word operators, their symbols and the logics that read them.**

| Word | Symbol | Read by |
| :--- | :--- | :--- |
| `not` | `!` | every logic |
| `and` | `&&` | every logic except NatSL |
| `or` | `\|\|` | every logic except NatSL |
| `implies` | `->` | every logic except NatSL |
| `next` | `X` | every logic except NatSL, TCTL |
| `eventually` | `F` | every logic except NatSL |
| `globally` | `G` | every logic except NatSL |
| `always` | `G` | every logic except NatSL |
| `until` | `U` | every logic except NatSL |
| `release` | `R` | CapATL, COTL, IATL, ICTL, OATL, OL, TOL |
| `weak` | `W` | COTL, OATL, OL, TOL |
| `forall` | `A` | CTL, ICTL, TCTL |
| `exist` | `E` | CTL, ICTL, TCTL |
| `with` | `:` | TOL |
| `is` | `is` | CapATL |

NatSL reads `not` before its goal (`E{1}x: (x, 1) not F p`) and takes no other
word, because its goal is one operator and one proposition
([the NatSL reference](NatSL/algorithm.md)). TCTL writes its clock
constraint with `:` only. CapATL reads `is` only
inside its knowledge operator, `K1(1 is c)`, and it has no symbol besides the word.

### Operators glued to a name

An operator written with no space before a name, such as `Fp`, is one word that
[rule 1](#names-and-keywords) refuses, never the operator applied to the name. It fails in one of three ways:

- Every logic except NatSL reads `Fp` as one word and refuses it by name, with `Atomic proposition 'Fp' is invalid`.
- IATL, TCTL and TOL give `Invalid character 'F'` for a word that starts with two capitals, such as `FFuel`, then refuse the rest (`Atomic proposition 'Fuel' is invalid`), because their lexer reads only a capital followed by a lowercase letter as the start of a word.
- NatSL rejects it with "Unsupported goal", so `Fgoal` is an error. A lowercase operator (`f goal`) is also an error ([rule 5](#names-and-keywords)).

### Lexer word patterns

Each parser's lexer reads a word (a run of letters, digits and `_`) with a pattern
wider than the name rule, so that `Goal` or `Fp` is read as one word and refused by
name, instead of `Fp` being read as `F p`. Most patterns are constants in
`syntax_patterns.py`:

- Every logic except IATL, TCTL, TOL, ATL* and NatSL, ICTL included:
  `PROPOSITION_TOKEN` = `[a-zA-Z][a-zA-Z0-9_]*` (Wallet_ATL writes the same pattern
  in its parser). `_goal` is therefore an `Invalid character '_'` error.
- ATL*: its grammar's own `IDENT` = `[a-zA-Z_][a-zA-Z0-9_]*`, so `_goal` is
  read as one word and refused by name.
- IATL, TCTL and TOL: `ICTL_PROPOSITION_TOKEN` (also named
  `TCTL_TOL_PROPOSITION_TOKEN`) = `[a-z][a-zA-Z0-9_]*` or
  `[A-Z][a-z][a-zA-Z0-9_]*`, so that `AF` and `EX` stay operators. `Goal` is
  refused by name; an all-capital word such as `P` or `GOAL` is an
  `Invalid character` error.
- NatSL temporal atoms: read with `[A-Za-z_][A-Za-z0-9_.]*` in its goal pattern
  (`NatSL/parser.py`), then checked with the name rule and the reserved-word rule; `true` and
  `false` are accepted as constants.

<a id="syntax-cards"></a>
## Syntax cards

Table 13 gives, for each logic, the prefix that scopes a formula, its temporal
operators as symbols, the model type it reads and one formula that parses. Word
forms are in [word operators](#word-operators), and the connectives and constants
in [Boolean logic](#boolean-logic-shared-syntax). The per-logic sections and
algorithm pages give the semantics. Each example parses; the NatSL one also checks
only on a 1-agent model (see [NatSL](#natsl---natural-strategy-logic)).

**Table 13: Syntax card of each logic.**

| Logic | Prefix | Operators | Model | Example |
| :--- | :--- | :--- | :--- | :--- |
| LTL | none | `X`, `F`, `G`, `U` | CGS | `G (p -> F q)` |
| CTL | `A`, `E` | `AX`, `AF`, `AG`, `EX`, `EF`, `EG`, `A[p U q]`, `E[p U q]` | CGS | `AG (p -> EF q)` |
| ICTL | `A`, `E` | as CTL, plus `R` in `A[p R q]`, `E[p R q]` | BirelationalMatrix | `E[p R q]` |
| TCTL | `A`, `E`; clock constraint `phi : x<5`; freeze `x.phi` | `AF`, `AG`, `EF`, `EG`, `A(p U q)`, `E(p U q)` (no brackets) | timedCGS | `AF p : x<5` |
| ATL | `<1,2>` | `X`, `F`, `G`, `U` | CGS | `<1,2>F p` |
| ATLF | `<1,2>` | `X`, `F`, `G`, `U` | CGS | `<1>(p U q)` |
| IATL | `<1,2>` exists, `[1,2]` for all | `X`, `F`, `G`, `U`, `R` | BCGS | `[1,2]F goal` |
| ATL_STAR | `<<1,2>>` | `X`, `F`, `G`, `U`, nested path formulas | CGS | `<<1>> (F p && G q)` |
| Wallet_ATL | `<<1>>`, `<<1:wallet(1,>=10)>>` | `X`, `F`, `G`, `U` | WalletCGS | `<<1:wallet(1,>=10)>>F p` |
| OATL | `<1,2><10>` | `X`, `F`, `G`, `U`, `R`, `W` | costCGS | `<1,2><10> (p W q)` |
| COTL | `<1,2><1>`, `<><0>` | `X`, `WX`, `F`, `G`, `U`, `R`, `W` | ObstructionModel | `<1,2><1> G !q` |
| RBATL | `<1><10,5>` | `X`, `F`, `G`, `U` | costCGS | `<1><10,5>F p` |
| RABATL | `<1><2,2>` | `X`, `F`, `G`, `U` | costCGS | `<1><2,2>F p` |
| NatATL | `<{1,2}, 5>` | `X`, `F`, `G`, `U` | CGS | `<{1,2}, 5>F p` |
| NatATL_Recall | `<{1,2}, 5>` | `X`, `F`, `G`, `U` | CGS | `<{1}, 3>G p` |
| NatATLF | `<{1,2}, 5>` | `X`, `F`, `G`, `U` | CGS | `<{1,2}, 5>F p` |
| CapATL | `<{1,2}>`; knowledge `K1(...)` | `X`, `F`, `G`, `U`, `R` | capCGS | `<{1}>F (g && K1(1 is c))` |
| OL | `<J5>` | `X`, `F`, `G`, `U`, `R`, `W` | costCGS | `<J5> (p R q)` |
| TOL | `{J5}`; clock constraint `phi : x<5`; freeze `x.phi` | `X`, `F`, `G`, `U`, `R`, `W` | timedCGS | `{J5}F x.(p : x<5)` |
| NatSL | `E{1}x A{1}y: (x, 1)(y, 2)` | one goal: `F`, `G` or `X` | CGS | `E{1}x: (x, 1) F goal` |

<a id="summary-logic-comparison-matrix"></a>
## Logic comparison matrix

The prefix, operators and model type of each logic are in the
[syntax cards](#syntax-cards); Table 14 adds what the cards leave out.

**Table 14: Path type and notes for each logic.**

| Logic | Path type | Notes |
| :--- | :--- | :--- |
| CTL | Branching | Path quantifiers `A`, `E` |
| LTL | Linear (sure-win) | No prefix |
| ATL | Branching | Coalition `<A>` with no bound |
| ATLF | Branching | Per-state values, not a set of states ([ATLF](ATLF/algorithm.md)) |
| ATL_STAR | Branching | Nested path formulas and coalitions inside `<<A>>`; no wallet guards |
| NatATL | Branching | Memoryless strategies; `k` is the strategy complexity |
| NatATL_Recall | Branching | As NatATL, with recall strategies |
| NatATLF | Branching | Delegates to the memoryless NatATL solver |
| NatSL | Branching | Schedule `space` (default) or `time` |
| OATL | Branching | Demon budget per step |
| OL | Linear | Demonic bound `<Jk>` |
| RBATL | Branching | Resource vector bound, flat action costs |
| RABATL | Branching | Resource vector bound, coalition-sum costs |
| CapATL | Branching | Knowledge operator `K1(...)` (the digit is the agent) |
| COTL | Branching | Legion of demons, budget per step |
| Wallet_ATL | Branching | Wallet guards in the coalition |
| ICTL | Branching | Intuitionistic `->` and `not` |
| IATL | Branching | Intuitionistic `->` and `!`; `[A]` is the universal coalition |
| TCTL | Branching | Clock constraints and freeze |
| TOL | Linear | Per-step obstruction, clock constraints and freeze |

<a id="model-syntax"></a>
## Model syntax

Each logic reads one model type, given in its [syntax card](#syntax-cards). The
sections of every model type, how a loader detects the type, and examples are in
[file_formats.md](file_formats.md#supported-model-types):

- [CGS](file_formats.md#cgs-sections): the base concurrent game structure.
- [costCGS](file_formats.md#costcgs-sections): CGS with action or edge costs.
- [capCGS](file_formats.md#capcgs-sections): CGS with capacities.
- [WalletCGS](file_formats.md#walletcgs-sections): CGS with one wallet per agent.
- [BirelationalMatrix](file_formats.md#birelationalmatrix-sections-ictl): ICTL's
  relation matrix.
- [BCGS](file_formats.md#bcgs-sections-iatl): CGS with a `Preorder` matrix.
- [timedCGS](file_formats.md#timedcgs-sections): costCGS with clocks.
- [ObstructionModel](file_formats.md#obstructionmodel-sections-cotl): COTL's graph
  with demons.

## Technical references

The theory in this page draws on these textbooks:

- Baier, C. & Katoen, J. P. (2008). _Principles of Model Checking_. MIT Press.
  It covers the theoretical foundations for CTL and LTL, state-space exploration,
  and labelling algorithms.
- Jamroga, W. (2015). _Specification of Multi-Agent Systems_. It covers strategic
  reasoning, ATL/NatATL foundations, and capacity-constrained logic formalisms.
