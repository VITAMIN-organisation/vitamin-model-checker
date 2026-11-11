# VITAMIN Model Checker - Logic Knowledge Base

## Overview

This is the **cross-logic theory and syntax map** for VITAMIN. For each logic it
covers:

1. **Theoretical background** - standard syntax and semantics from the literature.
2. **Current implementation** - surface grammar, model type, and how theory maps to code.
3. **Comparison** - short theory vs implementation table.
4. **Shared policies** - empty coalitions, proposition tokens, and model formats.

For denotations, fixpoints, validation proofs, and pipeline details, use the
per-logic `docs/<Logic>/algorithm.md` pages (for example
[ICTL/algorithm.md](ICTL/algorithm.md)). For how to author `.txt` models, use
[file_formats.md](file_formats.md).

## Per-logic algorithm pages

The algorithm pages are now split by logic so implementation details are easy
to locate:

- [CTL](CTL/algorithm.md)
- [LTL](LTL/algorithm.md)
- [ATL](ATL/algorithm.md)
- [ATLF](ATLF/algorithm.md)
- [ATL_STAR](ATL_STAR/algorithm.md)
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

**Logic names:** Full names are used for logics defined in the VITAMIN paper and standard references (CTL, LTL, ATL), and for OATL and COTL, whose sections cite their defining papers. Other implemented logics (OL, etc.) are listed by acronym only; their expansions are not fixed in the project literature.

---

## Table of Contents

1.  [Boolean Logic (Shared Syntax)](#boolean-logic-shared-syntax)
2.  [CTL - Computation Tree Logic](#ctl---computation-tree-logic)
3.  [LTL - Linear Temporal Logic](LTL/algorithm.md)
4.  [ATL / ATLF - Alternating-time Temporal Logic](ATL/algorithm.md)
5.  [NatATL / NatATLF](NatATL/algorithm.md)
6.  [NatSL](#natsl---natural-strategy-logic)
7.  [OATL](#oatl)
8.  [OL](#ol)
9.  [RBATL / RABATL](#rbatl--rabatl)
10. [CapATL](#capatl)
11. [COTL](#cotl)
12. [Wallet_ATL](#wallet_atl)
13. [ICTL](#ictl---intuitionistic-ctl)
14. [IATL](#iatl---intuitionistic-atl)
15. [TCTL](#tctl---timed-ctl)
16. [TOL](#tol---timed-obstruction-logic)
17. [Empty and Repeated Coalition Policy](#empty-coalition-policy)
18. [Atomic Proposition Policy](#atomic-proposition-policy)
19. [Model Syntax](#model-syntax)

---

<a id="boolean-logic-shared-syntax"></a>
## Boolean Logic (Shared Syntax)

All logics in VITAMIN share a common set of boolean operators and constants.

**Boolean Constants:**
- `true`: Constant true
- `false`: Constant false

**Boolean Operators (Ordered by Precedence):**

| Operator | Syntax | Keyword | Description |
| :--- | :--- | :--- | :--- |
| **Negation** | `!` | `not` | Logical NOT |
| **Conjunction** | `&&` | `and` | Logical AND |
| **Disjunction** | `\|\|` | `or` | Logical OR |
| **Implication** | `->` | `implies` | Logical implication (p -> q) |

Every logic spells the connectives this way. A single `&` or `|`, and `>` as
implication, are rejected in all of them (`test_connective_spelling.py`), so a
formula is never valid in one logic and invalid in another. NatSL goals take no
connectives.

**Grouping and Nesting:**

| syntax | Description | Supported Logics |
| :--- | :--- | :--- |
| `(...)` | Standard grouping | **All** logics |
| `[...]` | Around the Until of a path quantifier, `A[p U q]` (CTL, ICTL), or its Release, `E[p R q]` (ICTL) | CTL and ICTL only |

CTL writes square brackets only around an Until, `A[f1 U f2]`, and groups
everything else with parentheses (Clarke, Emerson, Sistla, ACM TOPLAS 1986,
p. 246). ICTL writes them once, around a Release (EUMAS 2025, p. 10), and ICTL
also takes them around an Until because its grammar treats U and R alike (see
[the ICTL reference](ICTL/algorithm.md)). `[p] && q` and `AF [p]` are syntax
errors, and so is `[...]` in every other logic.

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
readings, for `&&`, `||` and `->` in any spelling (`and`, `&`, `implies`):

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

Temporal operators (`X`, `F`, `G`, `U`, and in CTL and ICTL `AX`, `AF`, `AG`, `EX`, `EF`, `EG`; TCTL has no `X`, see [the TCTL reference](TCTL/algorithm.md)) are words of their own. Follow one with a space, `(` or `!`: `F p`, `F (p && q)`, `F !p`.

An operator written with no space before a name, such as `Fp` or `FFuel`, is part of that name, so no logic reads it as an operator applied to the name. A name that only starts with an operator letter, such as `Fuel` or `Goal`, is valid when it stands alone: in `F Fuel` the space makes `F` the operator and `Fuel` the name. A binary operator follows the same rule: `pUq` is one name, and `p U q` is the Until.

Every logic follows this rule, and `model_checker/tests/unit/parsers/formulas/test_operator_spacing.py` checks it for each registered logic. The form with no space fails in one of three ways:

- LTL and ATL* read it as one name, then report that the name is not among the model's declared propositions, with the name in the message. LTL checks every name, whatever its case or digits.
- NatSL rejects it: `Fgoal`, and a goal with no operator such as `Goal`, are errors. A lowercase operator (`f goal`) is also an error, because operators are uppercase.
- Every other parser reports a syntax error.

A name the model does not declare is an error in every logic, wherever it sits in the formula: under `!`, inside an Until or a conjunction. The error type is `semantic` (NatSL reports `validation`), so a typo never reads as a proposition that is false everywhere, which would make `AG !typo` true. The message names it: "Proposition(s) 'zz' not among the model's declared propositions [...]". `model_checker/tests/integration/algorithms/test_error_contract.py` checks this for each registered logic.

LTL, NatATL, NatATL_Recall and NatATLF check their goal and strategy conditions as CTL text, where `A` and `E` are path quantifiers. A model proposition named `A`, `E`, `AF` or another name the CTL parser reads as an operator is therefore refused by these four logics with a semantic error that names it; rename it in the model. The other logics accept such names.


**Truth Table:**

```text
   p   |   q   |  !p   | p && q | p || q | p -> q
-------|-------|-------|--------|--------|--------
 true  | true  | false |  true  |  true  |  true
 true  | false | false |  false |  true  |  false
 false | true  | true  |  false |  true  |  true
 false | false | true  |  false |  false |  true
```

---

<a id="ctl---computation-tree-logic"></a>
## CTL - Computation Tree Logic

### Theoretical Background

CTL is a branching-time logic defined over computation trees. Formulas are evaluated at a state and quantify over all possible infinite paths from that state.

**Standard Syntax:**
- **Path Quantifiers:**
    - `E`: There exists a path...
    - `A`: For all paths...
- **Temporal Operators:**
    - `X`: Next state
    - `F`: Eventually (finally)
    - `G`: Globally (always)
    - `U`: Until

**Standard Examples:**
- `AG p`: Always globally p (p is an invariant).
- `EF p`: Eventually p (reachability).
- `AG (p -> AF q)`: Always if p, then eventually q on all paths (liveness/response).

**Traces (optional):** With `generate_trace=True` the result has a `trace` for
the outermost operator of the formula at the initial state: a witness when an
operator that starts with `E` holds, a counterexample when one that starts with
`A` fails, and `None` otherwise. See [Traces](CTL/algorithm.md#traces) for each
case.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/CTL/parser.py`

**Algorithm:** `model_checker/algorithms/explicit/CTL/`

**Implemented Logic Support:**
- Path quantifiers `E` / `A` with temporal operators `X`, `F`, `G`, and `U`.
- Boolean connectives shared with the common formula syntax.
- Optional traces (`generate_trace=True`): a witness or a counterexample for the
  outermost operator, as described under "Traces (optional)" above.

See [CTL algorithm reference](CTL/algorithm.md) for denotations and operators.

---

<a id="natsl---natural-strategy-logic"></a>
## NatSL - Natural Strategy Logic

### Theoretical Background

NatSL quantifies over bounded natural strategies and binds those strategies to
agents. The current checker implements a restricted one-goal fragment.

**Standard Syntax:**
- Existential / universal strategy quantifiers with complexity bounds: `E{k}x`,
  `A{k}y`.
- Explicit agent bindings: `(x, 1)(y, 2)`.
- Temporal goals: `F`, `G`, `X`, and their negations.

A representative formula is:

```text
E{2}controller A{1}opponent: (controller, 1)(opponent, 2) F goal
```

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/NatSL/parser.py`

**Algorithm:** `model_checker/algorithms/explicit/NatSL/core.py`

**Implemented Logic Support:**
- Ordered prefixes of the form `E* A*`, including purely existential prefixes.
- Multi-character strategy variables and explicit agent bindings.
- A goal is an operator, a space and a proposition (`F goal`); see [operators and names](#operators-and-names).
- Exact action pruning (no idle-action fallback).
- Direct evaluation of mixed bounded prefixes (no NatATL decomposition).

### Execution schedules

Both schedules share the same acceptance semantics:

1. `mode="space"`: space-oriented lazy search.
2. `mode="time"`: time-oriented materialized search.

See [NatSL algorithm](NatSL/algorithm.md) and [NatSL semantics](NatSL/semantics.md).

---

<a id="oatl"></a>
## OATL

### Theoretical Background

OATL (Obstruction Alternating-time Temporal Logic) is defined in D. Catta,
J. Leneutre, V. Malvone, A. Murano, "Obstruction Alternating-time Temporal
Logic: a Strategic Logic to Reason about Dynamic Models", AAMAS 2024. Besides
the agents of a `costCGS`, a single extra player, the Demon, can temporarily
erase transitions. Erasing joint action `a` at state `s` costs `$(s, a)`.

**Standard Syntax:**
- **Bounded Coalition**: `[[A]]_n theta` in the paper, `<A><n> theta` in VITAMIN
    - `A`: the coalition of agents.
    - `n`: the Demon's budget per step.
- **Operators**: `X`, `U`, `R` are primitive; `F`, `G`, `W` are derived.

**Semantics:**
- `<A><n> theta` holds at `s` when the Demon has a strategy that, at each step,
  erases a set of joint actions of total cost at most `n` (never all of them),
  such that for every strategy of `A`, some remaining path satisfies `theta`.
  The agents outside `A` resolve the remaining choices in the Demon's favour.
- The budget applies to each step separately; it is not a sum along the path.
- Example: on the Figure 1 model of the paper
  (`tests/fixtures/costCGS/OATL/oatl_3agents_medium_6states_costs.txt`),
  `<1,2><2> G !(r && s && g)` is false at `s0` and `<1,2><3> G !(r && s && g)`
  is true: the least budget that stops the attack is 3, as the paper states.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/OATL/parser.py`

**Supported Syntax:**
1.  **Format**: `<coalition><budget>` (e.g., `<1,2><10>`).
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W` (and their keywords).
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.
4.  **Boolean Constants**: Supports `true` and `false`.

**Validation Rules:**
- **Budget Requirement**: A budget is mandatory for every coalition-prefixed temporal operator.
- **Budget Value**: The budget `n` is an integer `n >= 0` with no leading zeros. With `n = 0` the Demon can erase only zero-cost joint actions.
- **Parentheses**: Binary operators may be written as in the paper, `<A><n> (phi U psi)`, or without parentheses.

**Costs:** each `Costs_for_actions` entry gives the Demon's cost to erase that
joint action at that state. A cost vector (`1:2:0`) is summed into one cost.
A transition may have no cost; the check fails, naming the states and actions,
only when the result depends on those missing costs.

**Formula Examples:**
```text
<1><5> F goal
<1,2><10> (safe W unsafe)
<1,2><3> (false R !(r && s && g))
<1><0> X p
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | `[[A]]` | `<1,2>` (indices) |
| **Budget** | `n` in N, per step | `<n>` with `n >= 0`, per step |
| **Temporal Ops**| X, U, R (F, G, W derived) | `X`, `F`, `G`, `U`, `R`, `W` |
| **Algorithm** | Proposition 1 and Theorem 1 | `OATL/preimage.py` and fixpoints in `OATL/operators.py` |


---

<a id="ol"></a>
## OL

### Theoretical Background

OL (Obstruction Logic, ECAI 2023) is a game against a Demon on `costCGS` models: `<Jk> phi` holds when the Demon, with a budget of `k` at each step, can disable edges so that every remaining path satisfies `phi`. It is OATL with the coalition of all agents. The [OL algorithm reference](OL/algorithm.md) gives the rules and the sources.

**Standard Syntax:**
- **Cost prefix**: `<Jk> phi` where `k` is a natural number, 0 included.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/OL/parser.py`

**Supported Syntax:**
1.  **Format**: `<Jk>` (e.g., `<J5>`). The letter `J` is mandatory inside the angle brackets.
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W`.
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.

**Validation Rules:**
- **Mandatory `J`**: OL prefixes must use `<Jk>`, not bare `<k>`.
- **Bound requirement**: Every temporal operator must be prefixed with `<Jk>`.
- **Bound**: `k >= 0` with no leading zero; `<J0>` is valid and `<J01>` is rejected.

**Formula Examples:**
```text
<J5> F goal
<J10> G ok
<J3> (p U q)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Cost prefix** | `<Jk>` | `<Jk>` (requires `J`) |
| **Temporal ops** | X, F, G, U | X, F, G, U, R, W |
| **Cost semantics** | Demon budget `k` at each step | Same, through the OATL operators with the coalition of all agents |

---

<a id="rbatl--rabatl"></a>
## RBATL / RABATL

### Theoretical Background

RBATL and RABATL extend ATL with vector cost bounds on coalition strategies over `costCGS` models.

**Standard Syntax:**
- **Vector bounded coalition**: `<A><b1, b2, ...> phi`
    - `A`: coalition agents.
    - `b1, b2, ...`: per-resource bounds.

### Current Implementation

**Parser locations:** `RBATL/parser.py`, `RABATL/parser.py` (same surface syntax).

**Supported Syntax:**
1.  **Format**: `<coalition><bound1,bound2,...>` (e.g., `<1><10,5>`).
2.  **Temporal Operators**: `X`, `F`, `G`, `U` (`R`/`W` rejected at parser).
3.  **Multi-resource bounds**: comma-separated inside the second angle-bracket group.

**Cost models:**
- **RBATL** uses flat `Costs_for_actions` entries (`agent$cost:cost`).
- **RABATL** uses `Costs_for_actions_split` and sums coalition members' cost components when checking a joint action.

**Semantics (both):** On each coalition-controlled transition, resource `i` consumed must satisfy `cost_i <= b_i` (per-step affordability, not cumulative path totals).

**Formula Examples:**
```text
<1><100,50> F goal
<1,2><10,10,10> G safe
<1><5> (p U q)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | `<A>` | `<1,2>` (indices) |
| **Vector bound** | `<b1, b2, ...>` | `<10,5>` (comma-separated) |
| **Temporal ops** | X, F, G, U | `X`, `F`, `G`, `U` (R/W rejected at parser) |
| **RBATL costs** | Flat action costs | `Costs_for_actions` |
| **RABATL costs** | Split / coalition-sum | `Costs_for_actions_split` |

> [!NOTE]
> **RABATL is not a separate recursive-modality engine** in VITAMIN. It shares `bounded_atl_solver` with RBATL and differs only in how action costs are derived from the model file. Winning sets can differ from RBATL on the same formula when coalition-sum costs disagree with flat costs.

> [!NOTE]
> **Operator Support (R, W):** Release (`R`) and Weak Until (`W`) are rejected at parse time for RBATL/RABATL.

**Validation Rules:**
- **Comma separation**: resource vectors use commas, not colons.
- **Resource count**: bound vector length should match the cost dimension in the model.

---

<a id="capatl"></a>
## CapATL

### Theoretical Background

CapATL is designed for models with explicit capacity constraints (`capCGS`), often involving knowledge (capability) and agent-scoped properties.

**Standard Syntax:**
- **Coalition modality**: `<{A}> phi` (paper-style agent set; capacities constrain
  available actions via the `capCGS` model, not a formula numeric bound).
- **Knowledge**: K^a_cap(phi) (AAMAS 2024, grammar p. 125, meaning p. 126):
  "agent a knows that the capacity assignment verifies phi", where phi is a
  capacity assignment formula built from `a -> c` (agent `a` has capacity `c`),
  negation and conjunction.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/CapATL/parser.py`

**Supported Syntax:**
1.  **Coalition**: `<{agent1,agent2,...}>` (curly braces required; no `, k`).
2.  **Knowledge**: `K1(2 is c)`, `K2(!(3 is c) && 1 is cop)`, alias `kcap1(...)`,
    where `a is c` is the paper's `a -> c`. Accepted forms, errors and precedence
    are in [the CapATL reference](CapATL/algorithm.md#formula-language).
3.  **Temporal Operators**: `X`, `F`, `G`, `U`, and binary `R` (Release).

**Validation Rules:**
> [!NOTE]
> **Operator Support (W):** Weak Until (`W`) is not part of CapATL path syntax and remains unsupported. Release (`R`) is accepted as a binary operator (`<{A}> phi R psi`) and evaluated by the CapATL solver (greatest fixpoint).
- **Model Requirement**: Can only be verified against `capCGS` models.
- **Formula bound**: `<{A}, k>` is rejected (no numeric `k` in CapATL).

**Formula Examples:**
```text
<{1,2}> F g
<{1}> G a
<{1,2,3}> X a
<{1}> a R g
<{1}> false R g
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | ⟨A⟩ / `<{A}>` | `<{A}>` (braces required; no formula `k`) |
| **Capacities** | Model / knowledge | `capCGS` sections + Pre over capacity knowledge |
| **Knowledge** | K^a_cap(phi) | Parsed as `Ka(...)`; model checking returns a validation error that names the operator |
| **Temporal** | X, U, R (F/G sugar) | `X, F, G, U, R` (`W` unsupported) |


---

<a id="cotl"></a>
## COTL

### Theoretical Background

COTL (Coalition Obstruction Temporal Logic) is defined in D. Catta, J. Leneutre,
V. Malvone, A. Murano, "Coalition Obstruction Temporal Logic: A New Obstruction
Logic to Reason About Demon Coalitions", IJCAI 2025. It runs on an
`ObstructionModel`: a graph of states, with no agents, whose edges several
demons can temporarily disable. Each demon action has a cost, and the idle
action `*` costs 0. The attacker is the path itself.

**Standard Syntax:**
- **Legion modality**: `<<G>>_n theta` in the paper, `<G><n> theta` in VITAMIN
    - `G`: a set of demons (a legion), possibly empty.
    - `n`: the legion's budget per step, `n >= 0`.
- **Operators**: `X`, `X~` (weak next), `U`, `R` are primitive; `F`, `G`, `W` are derived.

**Semantics:** `<G><n> theta` holds when the legion has a strategy that, at
each step, picks one action per member of total cost at most `n`, such that
every path left by the disabled edges satisfies `theta`, whatever the other
demons do. A path may stop when every edge out of its last state is disabled.
Example: on the case-study attack graph of the paper
(`tests/fixtures/ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt`),
`<1,3><1> G !q` holds at `s0` and `<1,2><1> G !q` does not, as Sec. 5 states.

### Current Implementation

**Parser:** `COTLParser` (`model_checker/parsers/formulas/COTL/parser.py`).

**Supported Syntax:**
1.  **Format**: `<legion><budget>` (e.g., `<1,3><1>`, `<><0>`). Demon indices go from 1 to `Number_of_demons`.
2.  **Temporal Operators**: `X`, `WX` (weak next), `F`, `G`, `U`, `R`, `W`. Binary operators may be written `<G><n> (phi U psi)` or without parentheses.
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.

**Formula Examples:**
```text
<1,3><1> G !q
<1><2> WX safe
<><0> X p
<1,2><3> (p U q)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Legion** | `<<G>>`, any subset of demons | `<1,3>`, `<>` for the empty legion |
| **Budget** | `n` in N, per step | `<n>` with `n >= 0`, per step |
| **Weak next** | `X~` | `WX` |
| **Paths that stop** | Allowed | `G`, `R`, `W`, `WX` hold on them; `X`, `U`, `F` need a next state |

> [!NOTE]
> **COTL vs OATL:** both come from obstruction logic, but they share no checker
> code. In OATL a single Demon helps against a coalition of agents on a
> `costCGS` (see [OATL](#oatl)). In COTL a legion of demons acts against the
> other demons and the path, on an `ObstructionModel`.

---

<a id="wallet_atl"></a>
## Wallet_ATL

ATL with wallet-aware coalitions over `WalletCGS` models.

**Coalition syntax:** `<<agents[:wallet constraints]>>` followed by a temporal formula. The `<<>>` prefix is **mandatory** before `X`, `F`, `G`, or `U`; bare temporal operators without a coalition are rejected. Each wallet guard names a coalition agent, and every guard must hold; see [Wallet_ATL formula language](Wallet_ATL/algorithm.md#formula-language).

> [!NOTE]
> **Why `<<>>` instead of `<>`?** Plain ATL uses `<1>` for coalitions only. Wallet_ATL
> embeds optional balance guards (`:wallet(agent, op value)`) inside the same prefix,
> so the grammar uses a dedicated `<< ... >>` token. That avoids clashing with other
> bracket conventions in VITAMIN: OATL/RBATL `<1><5>` (coalition then cost bound),
> NatATL `<{1}, k>`, CapATL `<{1}>`, and OL `<Jk>`. OATL's two bracket groups are separate tokens;
> Wallet's double brackets are one nested delimiter around agents plus guards.

**Examples:**
```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50)>>G funded
```

**Temporal operators:** `X`, `F`, `G`, `U`.

**Model type:** `WalletCGS`. See [Wallet_ATL usage](Wallet_ATL/usage.md).

> [!NOTE]
> **Wallet guards:** a guard is checked against the balances in the `Wallets`
> section at the state where a coalition move starts. Balances are not
> recomputed along transitions. Where each operator checks the guard is in
> [Wallet_ATL operators](Wallet_ATL/algorithm.md#operators).

A joint move is available only when every agent can pay for its part, so a
`D20` move needs at least 20 in the acting agent's wallet. The rules are in
[Wallet_ATL algorithm](Wallet_ATL/algorithm.md#semantic-denotations).

---

<a id="ictl---intuitionistic-ctl"></a>
## ICTL - Intuitionistic CTL

### Theoretical Background

ICTL (Intuitionistic CTL) extends CTL with **intuitionistic propositional
connectives** over **birelational models** (EUMAS 2025, Bozzelli et al.). Each
model has two relations on the same finite state set:

- **`P` (`<=_P`)**: information preorder; truth is monotone as knowledge grows.
- **`R`**: serial transition relation; path quantifiers range over infinite `R`-paths.

Path formulas (`X`, `U`, `R`) use standard CTL semantics on `R`-paths. Only
implication and negation are intuitionistic: `phi -> psi` is checked at all
`P`-refinements of the current state.

**Well-behaved frames (paper):** confluence constraints **C1** and **C2** between
`P` and `R` (EUMAS Def. 1). See [ICTL/algorithm.md](ICTL/algorithm.md).

**Standard syntax (state formulas):**
- Boolean: `->`, `not`, `/\`, `\/` (implication is primitive; no excluded middle).
- Path quantifiers: `E`, `A` over `R`-paths.
- Temporal: `X`, `U`, `R`; surface sugar `F` / `G` after `E` or `A`.

**Sugar encodings (EUMAS25b fixpoints):**
- `EF phi` = `E(T U phi)`
- `EG phi` = `E(bottom R phi)`
- `AF phi` = `A(T U phi)`
- `AG phi` = `A(bottom R phi)`

Classical CTL complement dualities (for example `AF phi` as `S \\ EG(~phi)`) are
**not valid** in ICTL and are not used by the checker.

### Current Implementation

**Parser:** `model_checker/parsers/formulas/ICTL/parser.py` (`ICTLParser`)

**Checker:** `model_checker/algorithms/explicit/ICTL/`

**Model loader:** `parsers/game_structures/birelational_matrix/`
(`BirelationalMatrix`, a `CGS` subclass). Cell labels: `0`, `R`, `P`, `P,R`.
Diagonal cells should be `P` or `P,R` so reflexivity of `P` holds. Metadata:
`model_type: "BirelationalMatrix"`.

**Supported syntax:**
1. **Quantifiers:** `E` / `exist`, `A` / `forall`.
2. **Temporal:** `X`, `U`, `R`; sugar `F` / `G` (also `eventually`, `globally`, etc.).
3. **Boolean:** `&&`, `||`, `!` / `not`, `->` / `implies`.
4. **Propositions:** standard alphabet `[a-zA-Z][a-zA-Z0-9_]*`. Path/temporal
   tokens (`E`, `A`, `X`, `F`, `G`, `U`, `R`, keywords) are lexed separately so
   forms such as `EX` / `AG` are operators, not atoms.

**Semantic highlights (set-based model checking):**
- `phi -> psi`, `not phi`: upward closure (`^up`) along `P`.
- `EX phi`: `Pre_exists([[phi]])`; `AX phi`: `Pre_forall([[phi]])` (no `^up` on `AX`).
- `EU` / `AU` / `ER` / `AR`: least / greatest fixpoints per EUMAS25b Theorem 3.
- `EF` / `EG` / `AF` / `AG`: direct fixpoint encodings above (not complement tricks).

**Formula examples:**
```text
EX e
EF e
AX e
AF e
AG (p -> EF q)
AG Goal
E p R q
!(e -> h)
```

**Model type:** `BirelationalMatrix`. Algorithm, C1/C2 validation, and denotations:
[ICTL/algorithm.md](ICTL/algorithm.md).

### Comparison: Theory vs Implementation

| Aspect | Theory (EUMAS25b) | Implementation |
| :--- | :--- | :--- |
| **Model** | Birelational frame + monotone valuation | `BirelationalMatrix` + `check_conditions_hold` |
| **Frame constraints** | C1, C2 (well-behaved) | C1, C2 (EUMAS Def. 1); no paper C3 |
| **`->`, `not`** | Intuitionistic (`^up`) | `handle_implies`, `handle_not` with `^up` |
| **`AX`** | `Pre_forall([[phi]])` | `handle_ax` = `Pre_forall` (no `^up`) |
| **`AF` / `AG`** | `A(T U phi)` / `A(bottom R phi)` | `handle_af` / `handle_ag` (direct fixpoints) |
| **`EF` / `EG` / `EU` / `AU` / `ER` / `AR`** | Standard fixpoints on `R` | Same as paper Figure 7 |
| **Complexity** | `O(|M|^2 * |phi|)` PTIME | Explicit set-based checker |

**Deep dive:** [ICTL/algorithm.md](ICTL/algorithm.md)

---

<a id="iatl---intuitionistic-atl"></a>
## IATL - Intuitionistic ATL

### Theoretical Background

IATL (Intuitionistic ATL) extends ATL with **intuitionistic propositional
connectives** and **dual coalition modalities** over BCGS models (Bozzelli et al.,
KR 2025). Each model combines:

- **CGS transitions**: joint action profiles (multi-agent moves).
- **Preorder `P`**: information refinement; intuitionistic truth is monotone along `P`.

**Coalition modalities** (surface syntax `<A>` / `[A]` for paper `<<A>>` / `[[A]]`):

- `<A> phi`: coalition `A` has a strategy enforcing `phi`.
- `[A] phi`: no strategy of `A` can prevent `phi`.

**Well-behaved BCGS (paper Definition 2):** per-coalition constraints **C1** and **C2**
(contravariant simulation of coalition decisions along `P`).

**Sugar encodings (KR 2025 fixpoints):**

- `<A> F phi` = `<A>(T U phi)`; `[A] F phi` = `[A](T U phi)`
- `<A> G phi` = `<A>(bottom R phi)`; `[A] G phi` = `[A](bottom R phi)`

On finitely-branching BCGS, perfect-recall and memoryless semantics coincide
(Theorem 5); the explicit checker uses memoryless coalition pre-images.

### Current Implementation

**Parser:** `model_checker/parsers/formulas/IATL/parser.py`

**Checker:** `model_checker/algorithms/explicit/IATL/`

**Model loader:** `parsers/game_structures/bcgs/` (`BCGS`, a `CGS` subclass).
Files use CGS `Transition` cells (joint actions) plus a boolean `Preorder`
section. Metadata: `model_type: "BCGS"`.

**Coalition pre-images (Proposition 2):**

- `Pre_d(A, X)` (`pre_exists`): some `A`-decision; all opponent responses stay in `X`.
- `Pre_f(A, X)` (`pre_forall`): every `A`-decision; some response lands in `X`.

**Semantic highlights:**

- `phi -> psi`, `! phi`: upward closure (`^up`) along `P`.
- `<A> X phi`: `Pre_d`; `[A] X phi`: `Pre_f` (no `^up` on `[A] X`).
- `U` / `R` / `F` / `G`: fixpoints per Theorem 4 (Figure 4).

**Examples:**
```text
<1>G a
[1,2]F goal
<1,2>U safe
<1>X p
[1]X p
!p
p -> q
```

**Model type:** `BCGS` with separate `Preorder` section. See
[IATL/algorithm.md](IATL/algorithm.md) for validation, denotations, and pipeline.

### Comparison: Theory vs Implementation

| Aspect | Theory (KR 2025) | Implementation |
| :--- | :--- | :--- |
| **Model** | BCGS + monotone valuation | `BCGS` + `check_conditions_hold` |
| **Frame constraints** | C1, C2 per coalition | `_check_well_behaved_c1/c2` |
| **`->`, `!`** | Intuitionistic (`^up`) | `handle_implies`, `handle_not` |
| **`[A] X`** | `Pre_f(A, [[phi]])` | `handle_coalition_next_forall` = `Pre_f` |
| **`<A> X`** | `Pre_d(A, [[phi]])` | `handle_coalition_next_exists` |
| **`F` / `G`** | `U` / `R` encodings above | Direct fixpoint handlers |
| **Strategies** | Perfect recall = memoryless (finitely branching) | State-based pre-images |
| **Complexity** | `O(|G|^2 * |phi|)` PTIME | Explicit set-based checker |

**Deep dive:** [IATL/algorithm.md](IATL/algorithm.md)

---

<a id="tctl---timed-ctl"></a>
## TCTL

Timed CTL over `timedCGS` models. Checking uses a zone graph as the symbolic RTS
and the `rsat` regional labelling algorithm.

**Quantifiers:** `A`, `E` with `F`, `G`, `U` (no `X` or release).

**Clocks:**

- Automaton clocks `X` from the model `Clocks` section.
- Formula clocks `Y` via **FREEZE** `j.phi` (reset `j` to `0`, paper `j.reset(phi)`).
- Guards: standalone `x <= 5` or attachment `phi : x <= c` on subformulas.

**Examples:**
```text
AG a
EF crossing
EF (p : x<=1)
j.(j<=7 U goal)
```

**Model type:** `timedCGS` (`TimedCGS.read_file`).

**Deep dive:** [TCTL/algorithm.md](TCTL/algorithm.md)

---

<a id="tol---timed-obstruction-logic"></a>
## TOL

Linear-style **Timed Obstruction Logic** with demonic cost prefixes over `timedCGS`
models (AAMAS 2025). At each step the Demon may deactivate outgoing transitions
whose total cost is at most `k`; the Adversary chooses a remaining edge.

**Demonic prefix:** `{Jk}` where `k` is a positive integer (paper notation `⟨k⟩`).

**Examples:**
```text
{J5}F a
{J10}G safe
{J3}(p U q)
j.(j<=7 U goal)
```

**Temporal operators:** `F`, `G`, `U`, `R`, `W` (paper); `X` (VITAMIN extension).

**Cost semantics:** `k` is a **per-position** demonic deactivation budget (paper
obstruction game), not cumulative path cost. OL (`<Jk>`) reads its budget the
same way.

**Freeze:** `j.phi` resets formula clock `j` to `0` at the current state.

**Model type:** `timedCGS`. Shares the `timed_cgs` parser with TCTL.

**Deep dive:** [TOL/algorithm.md](TOL/algorithm.md)

---

<a id="empty-coalition-policy"></a>
## Empty and Repeated Coalition Policy

VITAMIN does **not** support an empty strategic coalition written as `<>`. In ATL literature an empty coalition can be related to opponent-only or path-level reasoning; in this implementation that overlaps CTL existential quantification (`E`, `EF`, ...) without making the logic explicit.

**Policy:** reject `<> ...` in every logic. Use the correct surface for the property:

| Intent | Use | Do not use |
| :--- | :--- | :--- |
| Existential path reachability (CTL) | `EF p` | `<> F p` |
| Strategic coalition (ATL) | `<1> F p`, `<1,2> G p` | `<> F p` |
| Linear path eventually (LTL) | `F p` | `<> F p` |
| Cost-bounded strategy (OATL / RBATL) | `<1><5> F p` | `<> F p`, `<1> F p` without bound |
| Capacity / strategy-bound (NatATL) | `<{1}, 5> F p` | `<> F p` |
| Capacity coalition (CapATL) | `<{1}> F p` | `<> F p` |
| IATL universal coalition | `[1] G p` | `[] G p` (empty `[]` rejected) |

**Where rejection is enforced:**

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

VITAMIN also rejects a coalition that lists an agent twice, because a coalition is a set of agents (ATL, JACM 2002 p. 685, rule S3: A "is a set of players"). This holds in every logic whose coalition lists agents, including IATL's `[A]` and COTL's list of demons (its legion). For example, `<1,1> F p` in ATL and `<{2,1,2}> F p` in CapATL are errors that name the repeated agent.

---

<a id="atomic-proposition-policy"></a>
## Atomic Proposition Policy

Atomic identifiers for propositions and variables must follow a shared alphabet and must not clash with reserved syntax keywords.

**Standard alphabet (models and most logics):**
- Pattern: `[a-zA-Z][a-zA-Z0-9_]*` (`PROPOSITION_TOKEN` in `syntax_patterns.py`)
- Logics: CTL, LTL, ATL, ATL*, NatATL, NatSL, OATL, OL, RBATL, CapATL, COTL, ICTL,
  Wallet_ATL
- Examples: `p`, `Goal`, `safe_1`
- Validation: `validate_proposition_identifier()` in
  `model_checker/parsers/formulas/parser_utils.py`. It checks the propositions of
  CGS models and, in every logic, the propositions of a formula and the capacity
  names of a CapATL formula.

**Reserved keywords (case-insensitive):** `and`, `or`, `not`, `implies`, `until`, `release`, `globally`, `next`, `eventually`, `always`, `forall`, `exist`, `true`, `false`

`true` and `false` are the boolean constants, so a model that declares a proposition with
either name (`true`, `True`, `FALSE`, ...) is rejected when it is read. The constants
themselves are written in lowercase in a formula.

**Lexer-specific proposition patterns (modal compound disambiguation):**
- **IATL, TCTL, TOL**: `ICTL_PROPOSITION_TOKEN` /
  `TCTL_TOL_PROPOSITION_TOKEN` =
  `[a-z][a-zA-Z0-9_]*` or `[A-Z][a-z][a-zA-Z0-9_]*`. Mixed-case names such as
  `Goal` are supported; all-caps operator-shaped names and single uppercase
  letters (for example `P`) are not proposition tokens.
- **ICTL**: uses the standard alphabet above; `E` / `A` / temporal tokens are
  separate lexer rules (not the restricted `ICTL_PROPOSITION_TOKEN` pattern).
- **NatSL temporal atoms**: Use the standard alphabet above, including the
  reserved-word rule; `true` and `false` are accepted as constants. Single
  uppercase `E` / `A` are rejected after `F`, `G` or `X` because they are
  quantifier tokens in a NatSL formula.
- **CTL pre-validation**: Bare temporal operators at formula start are detected
  with token-boundary rules, so proposition names such as `Goal` or `Flux` are
  not mistaken for `G` / `F` operators.

**Known limitation (CTL, LTL, ATL, NatATL, and related logics):** A proposition whose name is exactly a modal operator token (for example `F`, `E`, or `EX`) may be unparseable in some positions because the lexer reads it as syntax. Prefer descriptive names (`Goal`, `safe_1`) over single-letter operator aliases.

---

<a id="summary-logic-comparison-matrix"></a>
## Summary: Logic Comparison Matrix

| Logic | Path Type | Key Operators | Coalitions / Bounds | Model Type |
| :--- | :--- | :--- | :--- | :--- |
| **CTL** | Branching | `AX`, `EF`, `AG`, `E(p U q)` | `A`, `E` (Quantifiers) | CGS |
| **LTL** | Linear (sure-win) | `X`, `F`, `G`, `U` | None | CGS |
| **ATL** | Branching | `<A>X`, `<A>F`, `<A>G`, `<A>U` | `<1,2>` | CGS |
| **ATLF** | Branching | `<A>X`, `<A>F`, `<A>G`, `<A>U` | `<1,2>` | CGS (Fixed-point) |
| **ATL_STAR** | Branching | `<<A>>` over nested path formulas (`X`/`F`/`G`/`U`, nested coalitions) | `<<1,2>>` (not Wallet_ATL's wallet guards) | CGS |
| **NatATL (ML)** | Branching | `<A,k>X`, `<A,k>F`, `<A,k>G`, `<A,k>U` | `<{1,2}, k>` (k = strategy complexity) | CGS |
| **NatATL (Rec)** | Branching | `<A,k>X`, `<A,k>F`, etc. | `<{1,2}, k>` (k = strategy complexity) | CGS |
| **NatATLF** | Branching | `<A,k>X`, `<A,k>F`, etc. | `<{1,2}, k>` | CGS (delegates to memoryless) |
| **NatSL** | Branching | `E{k}x`, `A{k}y`, `F`/`G`/`X` | `E{k}x A{m}y: (x, 1)(y, 2) F goal`; schedule `space`/`time` | CGS |
| **OATL** | Branching | `<A><k>X`, `F`, `G`, `U`, `R`, `W` | `<1,2><5>` (Demon budget per step) | costCGS |
| **OL** | Linear | `<Jk>X`, `F`, `G`, `U`, `R`, `W` | `<J5>` (Demonic) | costCGS |
| **RBATL** | Branching | `<A><b1,b2>X`, `F`, `G`, `U` | `<1><10,5>` (Vectors) | costCGS |
| **CapATL** | Branching | `<{A}>X`, `F`, `G`, `U`, `R`, `Ka(a is c)` | `<{1,2}>` | capCGS |
| **COTL** | Branching | `<G><n>X`, `WX`, `F`, `G`, `U`, `R`, `W` | `<1,3><1>`, `<><0>` (legion of demons, budget per step) | ObstructionModel |
| **Wallet_ATL** | Branching | `<<A>>X`, `F`, `G`, `U` | `<<1,2:wallet(...)>>` | WalletCGS |
| **ICTL** | Branching | `EX`, `AX`, `EF`, `AF`, `EG`, `AG`, `EU`, `AU`, `ER`, `AR` | `E`, `A`; `->` / `not` intuitionistic | BirelationalMatrix |
| **IATL** | Branching | `<A>X`, `<A>F/G/U/R`, `[A]X`, `[A]F/G/U/R` | `<1>` exist, `[1]` forall; `->` / `!` intuitionistic | BCGS |
| **TCTL** | Branching | `EF`, `AG`, clock bounds | `A`, `E` + clocks | timedCGS |
| **TOL** | Linear | `{Jk}X`, `F`, `G`, `U`, `R`, `W` | `{J5}` per-step obstruction | timedCGS |


---

<a id="model-syntax"></a>
## Model Syntax

VITAMIN supports several model formats. Content-based detection (for generic
loaders) and logic metadata (for `create_model_parser_for_logic`) both matter;
canonical authoring details are in [file_formats.md](file_formats.md).

### CGS (Concurrent Game Structure)
The base model for CTL, LTL, ATL, NatATL, NatSL, and related CGS logics.

**File Sections:**
1.  **Transition**: Matrix (States x States) of joint action profiles. Each non-zero cell lists one or more joints separated by commas. A joint is either compact (`AC` = agent 1 plays `A`, agent 2 plays `C`) or explicit (`A|C`, `IDLE|MOVE`). Both forms are the same per-agent move vector; checkers normalize them to `|`-separated profiles. Use `*` for a full-agent wildcard and `0` for no transition. Every state must have at least one successor (total relation); use a `*` self-loop on terminal states. Cost table keys are normalized to the same pipe form at load time.

    > **Why total transitions?** CTL/ATL (and related) semantics are defined on infinite paths (Baier/Katoen). A state with no successor makes `X` undefined and can make universal next operators hold vacuously. A self-loop means "stay here forever," not that the system has no end state in the modeled domain.
2.  **Unknown_Transition_by**: Typically zeroed matrix for experimental uncertainty.
3.  **Name_State**: Space-separated list of state names.
4.  **Initial_State**: The starting state identifier.
5.  **Atomic_propositions**: Space-separated list of available propositions.
6.  **Labelling**: Binary labelling matrix (States x Propositions).
7.  **Number_of_agents**: Total count of agents in the system.
8.  **Agent_labels** (optional): Whitespace-separated display names for agents
    1..n. Formulas use `<1>`, `<2>`, ...; labels are metadata only.

**Example Action Format:**
For 2 agents, `AC` and `A|C` both mean Agent 1 performs `A` and Agent 2 performs `C`. Prefer compact single-character names in examples; use `|` when an action name has more than one character.

### BirelationalMatrix (ICTL)
Used for ICTL. Loader:
`model_checker/parsers/game_structures/birelational_matrix/`.
Same sectioned layout as CGS, but `Transition` cells are relation labels
`0` / `R` / `P` / `P,R` (not joint actions). Metadata forces this type for ICTL;
generic content detection alone still sees an ordinary CGS-shaped file. See
[ICTL/algorithm.md](ICTL/algorithm.md).

### BCGS (Birelational Concurrent Game Structure)
Used for IATL. Loader: `model_checker/parsers/game_structures/bcgs/`.
CGS-style joint-action `Transition` matrix plus a boolean `Preorder` section
(`0`/`1`). Detected when a `Preorder` header is present. Metadata:
`model_type: "BCGS"`. See [IATL/algorithm.md](IATL/algorithm.md).

### costCGS (CGS with Costs)
Used for OATL, OL, RBATL and RABATL.
- **Section**: `Transition_With_Costs`
- **Format**: Same dimensions as the transition matrix. Cells contain cost vectors separated by colons (e.g., `1:2:0` for 3 agents).

### capCGS (CGS with Capacities)
Used for CapATL.
- **Section**: `Capacities` (list of capacity names).
- **Section**: `Capacities_assignment` (mapping matrix: Agents x Capacities).
- **Section**: `Actions_for_capacities` (maps resources directly to actions that consume/replenish them).

### WalletCGS (CGS with Wallets)
Used for Wallet_ATL.
- **Section**: `Wallets` - one line per state, `state: balance1 balance2 ...`. Every state needs a row; see [WalletCGS Sections](file_formats.md#walletcgs-sections).
- Extends standard CGS sections. Actions can encode wallet operations (for example `D20`, `B50`).

### timedCGS (Timed costCGS)
Used for TOL and TCTL. Includes all costCGS sections plus:
- **Section**: `Clocks` - clock variable names.
- **Section**: `Clock_constraints` - bounds and resets on transitions.
- **Section**: `Invariants` - clock invariants per state, with `<=` or `<` (a strict `x<3` excludes `x=3`; see [file_formats.md](file_formats.md)).

### ObstructionModel (COTL)
Used for COTL. Loader:
`model_checker/parsers/game_structures/obstruction_model/`. No agents: a 0/1
`Transition` matrix of edges (a state may have no successor), `Number_of_demons`,
`Demon_actions` (`demon state action cost`, idle `*` implicit at cost 0) and
`Curses` (`state a1,...,ak successor...`: the edges a joint demon action
disables). Detected when `Number_of_demons` is present. Format:
[file_formats.md](file_formats.md#obstructionmodel-sections-cotl).

---

## Technical References

The VITAMIN platform incorporates theoretical foundations from the following textbooks:

-   **Baier, C. & Katoen, J. P. (2008)**. _Principles of Model Checking_. MIT Press.
    -   *Coverage*: Theoretical foundations for CTL and LTL, state-space exploration, and labelling algorithms.
-   **Jamroga, W. (2015)**. _Specification of Multi-Agent Systems_.
    -   *Coverage*: Strategic reasoning, ATL/NatATL foundations, and capacity-constrained logic formalisms.

---

*This document serves as the official Logic Knowledge Base for the VITAMIN Model Checker.*


