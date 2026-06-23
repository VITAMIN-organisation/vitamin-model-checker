# VITAMIN Model Checker - Logic Knowledge Base

## Overview

This document provides a comprehensive knowledge base for all temporal logics implemented in the VITAMIN model checker. For each logic, it covers:

1.  **Theoretical Background**: Standard syntax and semantics from literature (e.g., Baier/Katoen and Jamroga).
2.  **Current Implementation**: Detailed grammar, supported keywords, and validation rules in VITAMIN.
3.  **Comparison**: Mapping between formal theory and implementation.
4.  **Model Syntax**: Requirements for writing models compatible with the logic.

**Logic names:** Full names are used only for logics defined in the VITAMIN paper and standard references (CTL, LTL, ATL). Other implemented logics (OATL, OL, COTL, etc.) are listed by acronym only; their expansions are not fixed in the project literature.

---

## Table of Contents

1.  [Boolean Logic (Shared Syntax)](#boolean-logic-shared-syntax)
2.  [CTL - Computation Tree Logic](#ctl---computation-tree-logic)
3.  [LTL - Linear Temporal Logic](#ltl---linear-temporal-logic)
4.  [ATL / ATLF - Alternating-time Temporal Logic](#atl--atlf---alternating-time-temporal-logic)
5.  [NatATL / NatATLF](#natatl--natatlf---natural-atl)
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
16. [TOL](#tol---timed-obligation-logic)
17. [Empty Coalition Policy](#empty-coalition-policy)
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
| **Conjunction** | `&&` or `&` | `and` | Logical AND |
| **Disjunction** | `\|\|` or `\|` | `or` | Logical OR |
| **Implication** | `->` or `>` | `implies` | Logical implication (p -> q) |

**Grouping and Nesting:**

| syntax | Description | Supported Logics |
| :--- | :--- | :--- |
| `(...)` | Standard grouping | **All** logics |
| `[...]` | Alternate grouping | **CTL ONLY** |

> [!NOTE]
> **Design Rationale:**
> - **CTL** supports `[...]` to maintain compatibility with standard academic notation (e.g., *Baier/Katoen*) where path formulas are traditionally enclosed in square brackets (e.g., `A[p U q]`).
> - **Other logics** (like ATL, NatSL, RBATL) use a variety of specialized brackets for coalitions `<...>`, capacities `{...}`, and bounds `{k}`. To maintain syntactic clarity and avoid "bracket fatigue," these parsers strictly use parentheses `(...)` for logical grouping.


> [!IMPORTANT]
> While parentheses `()` can be used in any logic to define precedence, square brackets `[]` are exclusively supported by the CTL parser. Using `[]` in LTL, ATL, or other logics will result in a syntax error.


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

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/CTL/parser.py`

**Supported Syntax:**
1.  **Quantifiers**: `E` (exist), `A` (forall).
2.  **Operators**: `X` (next), `F` (eventually), `G` (globally/always), `U` (until). Release (`AR`/`ER`) is **not** in the CTL surface syntax.
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*` (Letter start, then alphanumerics/underscores).
4.  **Grouping**: Parentheses `()` and square brackets `[]` are both supported. (Note: `[]` is unique to CTL).

**Validation Rules:**
- **Quantifier Requirement**: In CTL, every temporal operator (X, F, G, U) MUST be preceded by a path quantifier (A or E).
- **No coalition brackets**: CTL uses `E` / `A`, not ATL-style `<...>` coalitions. For existential reachability use `EF p`, not `<> F p` (empty `<>` is rejected in coalition logics and is not valid CTL syntax).
- **Propositions**: Cannot match reserved keywords like `and`, `or`, `exists`, etc.

**Formula Examples:**
```text
EX p
AX [p && q]
EF (p -> AG q)
A (p U q)
E (p U [q && AG r])
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Quantifiers** | E, A | `E`, `A` (also `exist`, `forall`) |
| **Temporal Ops** | X, F, G, U | `X`, `F`, `G`, `U` (also `next`, `eventually`, etc.) |
| **Boolean Ops** | AND, OR, NOT, IMPLIES | `&&`, `\|\|`, `!`, `->` (plus keywords) |
| **Grouping** | ( ) | `( )` and `[ ]` |
| **State Props** | p, Goal | `[a-zA-Z][a-zA-Z0-9_]*` |

---

<a id="ltl---linear-temporal-logic"></a>
## LTL

### Theoretical Background

In VITAMIN, LTL is implemented as **game-theoretic sure-win checking** over CGS models: the checker searches for a strategy profile that guarantees the formula on all plays consistent with that strategy (via strategy pruning and CTL-backed evaluation), not classical path-by-path LTL model checking on a single linear trace.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/LTL/parser.py`

**Supported Syntax:**
1.  **Operators**: `X`, `F`, `G`, `U` (and keyword aliases).
2.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.
3.  **No quantifiers**: `E`/`A` and coalition brackets are rejected.

**Validation Rules:**
- No coalitions or path quantifiers.
- `R` and `W` are **not** in the LTL surface syntax.

**Formula Examples:**
```text
G p
F (p && G q)
p U q
```

### Comparison: Theory vs Implementation

| Aspect | Classical path-LTL | VITAMIN implementation |
| :--- | :--- | :--- |
| **Semantics** | Single infinite path | Sure-win / strategy-based over CGS |
| **Path quantifiers** | None | None (enforced) |
| **Temporal ops** | X, F, G, U, R, W | `X`, `F`, `G`, `U` only |
| **Release / Weak** | R, W | Not supported |

---

<a id="atl--atlf---alternating-time-temporal-logic"></a>
## ATL / ATLF - Alternating-time Temporal Logic

### Theoretical Background

ATL extends CTL with coalition operators `[A]` (in VITAMIN written as `<A>`) to reason about the capabilities of agents. It is evaluated over Concurrent Game Structures (CGS).

**Standard Syntax:**
- **Coalition Operators:**
    - `<{1,2}> p`: Coalition of agents 1 and 2 has a strategy to ensure p.
- **Temporal Operators (same as CTL):** `X`, `F`, `G`, `U`.

**Semantics:**
- `<A> p` means agents in `A` have a strategy such that for all strategies of the other agents, `p` holds.
- **ATLF (Fixed-point ATL)**: Evaluated using fixed-point reasoning with real-valued semantics. Truth values are in the range `[0, 1]` rather than binary booleans.

**Standard Examples:**
- `<1> F win`: Agent 1 can eventually win regardless of others.
- `<1,2> G safe`: Agents 1 and 2 can maintain safety.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/ATL/parser.py`

**Supported Syntax:**
1.  **Coalition Syntax**: `<1,2>` (Angle brackets, comma-separated agent indices). Braces `{ }` are NOT used in the implementation's surface syntax for plain ATL.
2.  **Operators**: `X`, `F`, `G`, `U`.
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.
4.  **Validation**: Agent indices must be in range `[1, n_agent]`. Empty coalition `<>` is rejected.

**Formula Examples:**
```text
<1> F win
<1,2> G (p -> <3> F q)
<1> (p U q)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | <{1,2}> | `<1,2>` |
| **Temporal Ops** | X, F, G, U | `X`, `F`, `G`, `U` |
| **Propositions** | p, Goal | `[a-zA-Z][a-zA-Z0-9_]*` |
| **Valuation** | Binary (ATL) / [0,1] (ATLF) | Handled by model checker |

---

<a id="natatl--natatlf---natural-atl"></a>
## NatATL / NatATLF

### Theoretical Background

NatATL extends ATL with a bound `k` on **strategy complexity** (maximum condition-token depth in synthesized strategies), not on how many agents may act at once. **NatATLF** uses the same syntax and delegates to the NatATL Memoryless solver.

**Standard Syntax:**
- **Capacity Operator**: `<{A}, k> p`
    - `A`: A set of agents.
    - `k`: Positive integer bound on strategy complexity.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/NatATL/parser.py`

**Supported Syntax:**
1.  **Canonical Form**: `<{1,2}, 3>` (Angle brackets, curly braces for agent set, comma, then positive integer bound).
2.  **Operators**: `X`, `F`, `G`, `U`.
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.

**Validation Rules:**
- **Braces Required**: Unlike standard ATL, NatATL MUST use curly braces for the agent set `<{...}, k>`.
- **Bound Required**: The capacity bound `k` is mandatory.

**Formula Examples:**
```text
<{1,2}, 3> F goal
<{1}, 1> G active
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | <{A}, k> | `<{A}, k>` (Braces required) |
| **Bound k** | Strategy complexity | Mandatory integer (condition-token depth) |
| **Temporal Ops** | X, F, G, U | `X`, `F`, `G`, `U` |
| **Propositions** | p, Goal | `[a-zA-Z][a-zA-Z0-9_]*` |

### Memory Models and Variants

The behavior of agents in NatATL depends on the **Memory Model** selected during verification. These variants use the same syntax but different underlying algorithms in the VITAMIN engine:

1.  **NatATL Memoryless (Standard)**:
    - Agents act based only on the current state.
    - This matches the standard strategic reasoning of vanilla ATL and is typically the default behavior.
2.  **NatATL Recall**:
    - Agents can remember the full history of the path taken.
    - History-dependent strategies are often essential for satisfying complex capacity constraints that apply over multiple steps.
3.  **NatATL Recall Filter**:
    - Runs the same recall verification as NatATL Recall.
    - An ATL conversion step may run for diagnostics; **recall verification always runs**. ATL UNSAT does not short-circuit recall checking.

**Return contract:** NatATL Memoryless, Recall, and NatATLF report boolean `Satisfiability` plus `res` / `initial_state` (not CTL-style winning state sets).

---

<a id="natsl---natural-strategy-logic"></a>
## NatSL

### Theoretical Background

NatSL is a strategy logic incorporating natural language bindings and strategy quantifiers with explicit memory/resource bounds.

**Standard Syntax:**
- **Quantifiers:**
    - `Ex: p`: There exists a strategy `x` such that `p`.
    - `Ax: p`: For all strategies `x`, `p`.
    - `E{k}x: p`: Existential with bound `k`.
- **Bindings**: `(x, 1)` binds strategy `x` to agent `1`.
- **Separator**: `:` separates the quantifier/binding prefix from the temporal formula.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/NatSL/parser.py`

**Improved Logic Support:**
- **Identifiers**: Strategy variables and temporal atoms use the shared atomic proposition alphabet `[a-zA-Z][a-zA-Z0-9_]*` (same as CGS models and NatATL). Examples: `p`, `Goal`, `safe_1`, `win`.
- **Temporal operators**: The temporal expression is limited to `F` (Eventually) or `!F` (Not Eventually).

    > [!NOTE]
    > **Why only F / !F?** NatSL is currently implemented by reducing formulas to **NatATL**. While NatATL supports `G` (Globally) and `X` (Next), the NatSL engine is optimized for reachability properties.
    >
    > **Extensibility**:
    > - Support for **`G`** and **`X`** can be added in future versions as they map directly to single NatATL operators.
    > - Full **LTL** (nested operators like `G(p -> F q)`) is NOT currently planned for NatSL due to the extreme computational complexity (P-SPACE) and the memory-intensive nature of strategy logic verification. For complex temporal requirements, use the standard **LTL** or **CTL** logic types.
    >
    > **Parser edge case**: Temporal atoms cannot be the single uppercase letters `E` or `A` (NatSL quantifier tokens), and cannot match reserved keywords (`eventually`, `not`, etc.). All other valid model proposition names are accepted after `F` / `!F`.


**Syntax Components:**
1.  **Quantifier**: `E` or `A` followed by optional bound `{k}` and variable name.
2.  **Binding**: `(var, agent)` mapping.
3.  **Expression**: Only `F prop` or `!F prop`.

**Formula Examples:**
```text
E{3}x : (x, 1) F goal
Ax Ay : (x, 1)(y, 2) F win
E{2}myVar : (myVar, 1) !F fail
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Quantifiers** | Ex, Ax | `E{bound}x`, `A{bound}x` |
| **Variables** | Any identifier | `[A-Za-z_][A-Za-z0-9_]*` |
| **Propositions**| Any identifier | `[A-Za-z_][A-Za-z0-9_]*` (same rule for temporal atoms after `F` / `!F`) |
| **Temporal** | Full LTL/CTL | Only `F` or `!F` currently |
| **Reduced Form**| RED(SL) -> NatATL | Automatic conversion |

### Execution Semantics

NatSL supports two distinct semantic interpretations of strategy quantification sequences:

1.  **Sequential Semantics**:
    - Existential strategy quantifiers ($\exists$) are evaluated first to find a set of winning strategy trees. 
    - These candidate strategies are then validated against all possible universal counter-strategies ($\forall$) defined in the formula.
    - This reflects a "Proponent-first" view where a winning plan must be robust against any adversary.
2.  **Alternated Semantics**:
    - Verification alternates between existential search and universal validation at each step of the model exploration.
    - This reflects a "Game-theoretic" view where agents react to each other's moves dynamically.

---

<a id="oatl"></a>
## OATL

### Theoretical Background

OATL extends ATL with demonic cost bounds. It assesses whether a coalition can achieve a goal while keeping the total cost (defined in the model) below a specific threshold.

**Standard Syntax:**
- **Bounded Coalition**: `<A><k> p`
    - `A`: The coalition of agents.
    - `k`: A positive integer cost bound.
- **Operators**: Extends standard ATL with `W` (Weak Until) and `R` (Release).

**Semantics:**
- `<A><k> p` means coalition `A` has a strategy to ensure `p` such that for every sequence of actions, the sum of the costs is less than or equal to `k`.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/OATL/parser.py`

**Supported Syntax:**
1.  **Format**: `<coalition><bound>` (e.g., `<1,2><10>`).
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W` (and their keywords).
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.
4.  **Boolean Constants**: Supports `true` and `false`.

**Validation Rules:**
- **Bound Requirement**: A bound is mandatory for every coalition-prefixed temporal operator.
- **Positive Bound**: The bound `k` must be a positive integer (`k >= 1`) with no leading zeros.

**Formula Examples:**
```text
<1><5> F goal
<1,2><10> (safe W unsafe)
<3><2> G stable
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | <A> | `<1,2>` (Indices) |
| **Cost Bound** | <k> | `<k>` (Mandatory) |
| **Temporal Ops**| X, F, G, U | `X`, `F`, `G`, `U`, `R`, `W` |
| **Propositions**| p, Goal | `[a-zA-Z][a-zA-Z0-9_]*` |

> [!NOTE]
> **Operator Support (R, W):** Release (`R`) and Weak Until (`W`) are **rejected at parse time** for OATL. Use dual forms (for example `!<1><5> (!p U !q)`) or use COTL when R/W operators are required.

> **Cost bound semantics:** Bound `k` limits the cost of each individual transition (per-step affordability), not the cumulative sum along a play.
>
> **Example:** A property like `<1><5> (p R q)` would otherwise need to be written as `<1><5> !(!p U !q)` or `(<1><5> (q U (p && q)) || <1><5> G q)`, which is significantly less readable.


---

<a id="ol"></a>
## OL

### Theoretical Background

OL is the linear-time cost-bounded logic paired with OATL on `costCGS` models. Formulas use a demonic cost prefix `<Jk>` before temporal operators.

**Standard Syntax:**
- **Cost prefix**: `<Jk> phi` where `k` is a positive integer bound.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/OL/parser.py`

**Supported Syntax:**
1.  **Format**: `<Jk>` (e.g., `<J5>`). The letter `J` is mandatory inside the angle brackets.
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W`.
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.

**Validation Rules:**
- **Mandatory `J`**: OL prefixes must use `<Jk>`, not bare `<k>`.
- **Bound requirement**: Every temporal operator must be prefixed with `<Jk>`.
- **Positive bound**: `k >= 1`; `<J0>` is rejected.

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
| **Cost semantics (F/G/U/R/W)** | Path budget | **Accumulated** path cost `<= k` |
| **Cost semantics (X)** | Step budget | **Per-step** transition cost `<= k` |

> [!NOTE]
> **Cost bound semantics:** For `F`, `G`, `U`, `R`, and `W`, bound `k` limits the **sum of transition costs along the considered path**. For `X`, `k` limits only the **next** transition. This differs from OATL, where every operator uses per-step affordability.

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
- **Capacity Operator**: `<{A}, k> p`
    - `A`: A set of agents.
    - `k`: A positive integer bound on the total capacity utilized.
- **Knowledge (Capability)**: `Ki p` (Agent `i` has the capability/knowledge of `p`).
- **Agent Property**: `i is prop` (Agent `i` currently possesses property `prop`).

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/CapATL/parser.py`

**Supported Syntax:**
1.  **Coalition**: `<{agent1,agent2,...}, k>` (Must use curly braces).
2.  **Capability**: `K1(p)`, `K2(K3 p)`.
3.  **Agent Properties**: `1 is active`, `2 is critical`.
4.  **Temporal Operators**: `X`, `F`, `G`, `U` only.

**Validation Rules:**
> [!NOTE]
> **Operator Support (W, R):** Weak Until (`W`) and Release (`R`) are **rejected at parse time**. The CapATL solver evaluates `X`, `F`, `G`, and `U` only.
- **Model Requirement**: Can only be verified against `capCGS` models.

**Formula Examples:**
```text
<{1,2}, 3> F (K1 safe)
<{1}, 1> G (1 is active && ! 2 is active)
<{1,2,3}, 2> X (3 is standby)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | <{A}, k> | `<{A}, k>` (Braces required) |
| **Capability** | Ki p | `Ki (agent is p)` or `Ki(Ki agent is p)` |
| **Agent Prop** | i is p | `i is p` |
| **Temporal** | Full | `X, F, G, U` (`R`, `W` rejected at parser) |


---

<a id="cotl"></a>
## COTL

### Theoretical Background

COTL is the cost-bounded ATL logic used with `costCGS` models. Formulas share the OATL surface syntax `<A><k> phi` but are checked by a dedicated fixpoint engine (`COTL/COTL.py`), not by OATL per-step filtering.

### Current Implementation

**Parser:** `COTLParser` (`model_checker/parsers/formulas/COTL/parser.py`), same `<coalition><bound>` shape as OATL.

**Supported Syntax:**
1.  **Format**: `<coalition><bound>` (e.g., `<1,2><5>`).
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W` (R/W implemented in the COTL solver).
3.  **Propositions**: `[a-zA-Z][a-zA-Z0-9_]*`.

**Semantics:** Coalition `<A><k>` requires that coalition `A` can enforce the sub-formula while keeping transition costs within bound `k` under the COTL cost interpretation (cost-bounded strategy synthesis via least/greatest fixpoints, not OATL per-step filtering).

**Formula Examples:**
```text
<1><10> F goal
<1,2><5> (p U q)
<1><2> G safe
<1><5> (p R q)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | `<A>` | `<1,2>` (indices) |
| **Cost bound** | `<k>` | `<5>` (integer) |
| **Temporal ops** | X, F, G, U | `X`, `F`, `G`, `U`, `R`, `W` |
| **Engine** | Cost-bounded ATL | Dedicated COTL fixpoints (not OATL solver) |

> [!NOTE]
> **COTL vs OATL:** Same parser shape, different checker. OATL uses per-step affordability in `OATL/preimage.py` and rejects R/W. COTL uses its own fixpoint operators and accepts R/W.

---

<a id="wallet_atl"></a>
## Wallet_ATL

ATL with wallet-aware coalitions over `WalletCGS` models.

**Coalition syntax:** `<<agents[:wallet constraints]>>` followed by a temporal formula. The `<<>>` prefix is **mandatory** before `X`, `F`, `G`, or `U`; bare temporal operators without a coalition are rejected.

> [!NOTE]
> **Why `<<>>` instead of `<>`?** Plain ATL uses `<1>` for coalitions only. Wallet_ATL
> embeds optional balance guards (`:wallet(agent, op, value)`) inside the same prefix,
> so the grammar uses a dedicated `<< ... >>` token. That avoids clashing with other
> bracket conventions in VITAMIN: OATL/RBATL `<1><5>` (coalition then cost bound),
> NatATL/CapATL `<{1}, k>`, and OL `<Jk>`. OATL's two bracket groups are separate tokens;
> Wallet's double brackets are one nested delimiter around agents plus guards.

**Examples:**
```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50)>>G funded
```

**Temporal operators:** `X`, `F`, `G`, `U`.

**Model type:** `WalletCGS`. See [Wallet_ATL usage](Wallet_ATL/usage.md).

---

<a id="ictl---intuitionistic-ctl"></a>
## ICTL

Intuitionistic branching-time logic over **birelational models**: a preorder `P`
(information growth) and a serial transition relation `R` (system evolution) on
the same state set. This is **not** a standard CGS file; models use an `N x N`
matrix with cell labels `0`, `R`, `P`, `P,R`.

**Quantifiers:** `E` / `exist`, `A` / `forall` (path quantifiers over `R`-paths).

**Temporal operators:** `X`, `F`, `G`, `U`, `R` (`F`/`G` are parser sugar).

**Examples:**
```text
EX e
EF e
AG (p -> EF q)
AG Goal
E p R q
```

**Proposition lexer note:** ICTL uses a dedicated proposition pattern so path-operator
tokens such as `EX` and `AG` are not parsed as atomic names. Mixed-case identifiers
like `Goal` are supported. Single uppercase letters (for example `P`) are not valid
proposition tokens; use `p` or a mixed-case name such as `Prop` instead.

**Model type:** birelational matrix (loaded by `ICTL/util/graph.read_file`).
Metadata entry point lists `CGS` for VMI compatibility; see
[ICTL Algorithm](ICTL/algorithm.md) for theory, validation (C1/C2/C3), and the
model-checking algorithm.

**Deep dive:** [ICTL/algorithm.md](ICTL/algorithm.md)

---

<a id="iatl---intuitionistic-atl"></a>
## IATL

Coalition logic with intuitionistic existential and universal coalitions.

**Coalition syntax:**
- Existential: `<1,2>` (angle brackets)
- Universal: `[1,2]` (square brackets)

**Examples:**
```text
<1>G a
[1,2]F goal
<1,2>U safe
```

**Temporal operators:** `X`, `F`, `G`, `U`, `R`.

**Model type:** BCGS (CGS transitions plus a boolean `Preorder` matrix). Loaded by
`IATL/util/graph.read_file`.

**Deep dive:** [IATL/algorithm.md](IATL/algorithm.md)

---

<a id="tctl---timed-ctl"></a>
## TCTL

Timed extension of CTL over `timedCGS` models with clock constraints.

**Quantifiers:** `A`, `E` with `F`, `G`, `U` (no `X` or release in the parser).

**Clock constraints:** attach bounds to propositions, for example `x <= 5` or `t: formula`.

**Examples:**
```text
AG a
EF crossing
AG (x <= 10 -> safe)
```

**Model type:** `timedCGS` (loaded by `TimedCGS.read_file`).

**Deep dive:** [TCTL/algorithm.md](TCTL/algorithm.md)

---

<a id="tol---timed-obligation-logic"></a>
## TOL

Linear-style timed logic with demonic cost prefixes over `timedCGS` models.

**Demonic prefix:** `{Jk}` where `k` is a positive integer cost bound.

**Examples:**
```text
{J5}F a
{J10}G safe
{J3}(p U q)
```

**Temporal operators:** `X`, `F`, `G`, `U`, `R`, `W`.

**Model type:** `timedCGS`. Shares the `timed_cgs` parser with TCTL.

**Deep dive:** [TOL/algorithm.md](TOL/algorithm.md)

---

<a id="empty-coalition-policy"></a>
## Empty Coalition Policy

VITAMIN does **not** support an empty strategic coalition written as `<>`. In ATL literature an empty coalition can be related to opponent-only or path-level reasoning; in this implementation that overlaps CTL existential quantification (`E`, `EF`, ...) without making the logic explicit.

**Policy:** reject `<> ...` in every logic. Use the correct surface for the property:

| Intent | Use | Do not use |
| :--- | :--- | :--- |
| Existential path reachability (CTL) | `EF p` | `<> F p` |
| Strategic coalition (ATL) | `<1> F p`, `<1,2> G p` | `<> F p` |
| Linear path eventually (LTL) | `F p` | `<> F p` |
| Cost-bounded strategy (OATL / RBATL) | `<1><5> F p` | `<> F p`, `<1> F p` without bound |
| Capacity-bound strategy (NatATL / CapATL) | `<{1}, 5> F p` | `<> F p` |
| IATL universal coalition | `[1] G p` | `[] G p` (empty `[]` rejected) |

**Where rejection is enforced:**

| Logic | Coalition form | Empty coalition |
| :--- | :--- | :--- |
| ATL / ATLF | `<1>`, `<1,2>` | `<> ` rejected (precheck + parser) |
| IATL | `<1>` exist, `[1]` forall | `<> ` and `[]` rejected |
| NatATL | `<{1,2}, k>` | `<\s*>` rejected |
| CapATL | `<{1,2}, k>` | `<\s*>` rejected |
| OATL / COTL | `<1><5>` | `<\s*>` rejected; bound required |
| RBATL / RABATL | `<1><5>` or `<1><2,2>` | `<\s*>` rejected; bound required |
| OL | `<J5>` (cost, not agents) | N/A |
| Wallet_ATL | `<<1>>` | `<<>>` invalid (lexer) |
| CTL / LTL | `E` / `A` or none | `<> ` invalid syntax |

---

<a id="atomic-proposition-policy"></a>
## Atomic Proposition Policy

Atomic identifiers for propositions and variables must follow a shared alphabet and must not clash with reserved syntax keywords.

**Standard alphabet (models and most logics):**
- Pattern: `[a-zA-Z][a-zA-Z0-9_]*`
- Logics: CTL, LTL, ATL, NatATL, NatSL, OATL, OL, RBATL, CapATL, COTL, IATL, Wallet_ATL
- Examples: `p`, `Goal`, `safe_1`
- Validation: `validate_proposition_identifier()` in `model_checker/parsers/formulas/parser_utils.py` (CGS models and Family-B formula AST post-validation via `validate_ast()`)

**Reserved keywords (case-insensitive):** `and`, `or`, `not`, `implies`, `until`, `release`, `globally`, `next`, `eventually`, `always`, `forall`, `exist`

**Lexer-specific proposition patterns (modal compound disambiguation):**
- **ICTL, TCTL, TOL**: `[a-z][a-zA-Z0-9_]*` or `[A-Z][a-z][a-zA-Z0-9_]*` so tokens like `EX`, `EF`, and `AG` are not read as proposition names. Mixed-case names such as `Goal` are supported; all-caps operator-shaped names and single uppercase letters (for example `P`) are not.
- **NatSL temporal atoms**: Use the standard alphabet above. Single uppercase `E` / `A` are rejected after `F` / `!F` because they are quantifier tokens in the NatSL lexer.
- **CTL pre-validation**: Bare temporal operators at formula start are detected with token-boundary rules, so proposition names such as `Goal` or `Flux` are not mistaken for `G` / `F` operators.

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
| **NatATL (ML)** | Branching | `<A,k>X`, `<A,k>F`, `<A,k>G`, `<A,k>U` | `<{1,2}, k>` (k = strategy complexity) | CGS |
| **NatATL (Rec)** | Branching | `<A,k>X`, `<A,k>F`, etc. | `<{1,2}, k>` (k = strategy complexity) | CGS |
| **NatATLF** | Branching | `<A,k>X`, `<A,k>F`, etc. | `<{1,2}, k>` | CGS (delegates to memoryless) |
| **NatSL (Seq)** | Branching | `Ex`, `Ax`, `F`, `!F` | `Ex:{k}x:(x,1)` (Sequential) | CGS |
| **NatSL (Alt)** | Branching | `Ex`, `Ax`, `F`, `!F` | `Ex:{k}x:(x,1)` (Alternated) | CGS |
| **OATL** | Branching | `<A><k>X`, `F`, `G`, `U` | `<1,2><5>` (per-step cost bound) | costCGS |
| **OL** | Linear | `<Jk>X`, `F`, `G`, `U`, `R`, `W` | `<J5>` (Demonic) | costCGS |
| **RBATL** | Branching | `<A><b1,b2>X`, `F`, `G`, `U` | `<1><10,5>` (Vectors) | costCGS |
| **CapATL** | Branching | `<A,k>X`, `F`, `G`, `U`, `Ki`, `i is p` | `<{1,2}, k>` | capCGS |
| **COTL** | Branching | `<A><k>X`, `F`, `G`, `U`, `R`, `W` | `<1,2><k>` (cost-bounded) | costCGS |
| **Wallet_ATL** | Branching | `<<A>>X`, `F`, `G`, `U` | `<<1,2:wallet(...)>>` | WalletCGS |
| **ICTL** | Branching | `EX`, `AX`, `EF`, `AG`, `EU` | `E`, `A` | BCGS (birelational) |
| **IATL** | Branching | `<A>X`, `F`, `G`, `U` | `<1>` exist, `[1]` forall | BCGS |
| **TCTL** | Branching | `EF`, `AG`, clock bounds | `A`, `E` + clocks | timedCGS |
| **TOL** | Linear | `{Jk}X`, `F`, `G`, `U` | `{J5}` demonic bound | timedCGS |


---

<a id="model-syntax"></a>
## Model Syntax

VITAMIN supports six model formats. The parser picks the type from the
sections present in the file. Canonical details also appear in [file_formats.md](file_formats.md).

### CGS (Concurrent Game Structure)
The base model for CTL, LTL, ATL, NatATL, and NatSL.

**File Sections:**
1.  **Transition**: Matrix (States x States) containing joint action strings (e.g., `AC,AD`). Use `*` for wildcards and `0` for no transition.
2.  **Unknown_Transition_by**: Typically zeroed matrix for experimental uncertainty.
3.  **Name_State**: Space-separated list of state names.
4.  **Initial_State**: The starting state identifier.
5.  **Atomic_propositions**: Space-separated list of available propositions.
6.  **Labelling**: Binary labelling matrix (States x Propositions).
7.  **Number_of_agents**: Total count of agents in the system.
8.  **Agent_labels** (optional): Whitespace-separated display names for agents
    1..n. Formulas use `<1>`, `<2>`, ...; labels are metadata only.

**Example Action Format:**
For 2 agents: `AC` means Agent 1 performs action `A` and Agent 2 performs action `C`.

### BCGS (Birelational CGS)
Used for ICTL and IATL. Includes a `Preorder` matrix with edge labels (`P`, `R`, `P,R`).
Loader: `model_checker/parsers/game_structures/birelational/`.

### costCGS (CGS with Costs)
Used for OATL, OL, RBATL, RABATL, and COTL.
- **Section**: `Transition_With_Costs`
- **Format**: Same dimensions as the transition matrix. Cells contain cost vectors separated by colons (e.g., `1:2:0` for 3 agents).

### capCGS (CGS with Capacities)
Used for CapATL.
- **Section**: `Capacities` (list of capacity names).
- **Section**: `Capacities_assignment` (mapping matrix: Agents x Capacities).
- **Section**: `Actions_for_capacities` (maps resources directly to actions that consume/replenish them).

### WalletCGS (CGS with Wallets)
Used for Wallet_ATL.
- **Section**: `Wallets` - one line per state, `state: balance1 balance2 ...`.
- Extends standard CGS sections. Actions can encode wallet operations (for example `D20`, `B50`).

### timedCGS (Timed costCGS)
Used for TOL and TCTL. Includes all costCGS sections plus:
- **Section**: `Clocks` - clock variable names.
- **Section**: `Clock_constraints` - bounds and resets on transitions.
- **Section**: `Invariants` - clock invariants per state.

---

## Technical References

The VITAMIN platform incorporates theoretical foundations from the following textbooks:

-   **Baier, C. & Katoen, J. P. (2008)**. _Principles of Model Checking_. MIT Press.
    -   *Coverage*: Theoretical foundations for CTL and LTL, state-space exploration, and labelling algorithms.
-   **Jamroga, W. (2015)**. _Specification of Multi-Agent Systems_.
    -   *Coverage*: Strategic reasoning, ATL/NatATL foundations, and capacity-constrained logic formalisms.

---

*This document serves as the official Logic Knowledge Base for the VITAMIN Model Checker.*


