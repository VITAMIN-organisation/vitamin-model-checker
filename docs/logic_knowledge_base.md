# VITAMIN Model Checker - Logic Knowledge Base

## Overview

This document provides a comprehensive knowledge base for all temporal logics implemented in the VITAMIN model checker. For each logic, it covers:

1.  **Theoretical Background**: Standard syntax and semantics from literature (e.g., Baier/Katoen and Jamroga).
2.  **Current Implementation**: Detailed grammar, supported keywords, and validation rules in VITAMIN.
3.  **Comparison**: Mapping between formal theory and implementation.
4.  **Model Syntax**: Requirements for writing models compatible with the logic.

---

## Table of Contents

1.  [Boolean Logic (Shared Syntax)](#boolean-logic-shared-syntax)
2.  [CTL - Computation Tree Logic](#ctl---computation-tree-logic)
3.  [LTL - Linear Temporal Logic](#ltl---linear-temporal-logic)
4.  [ATL / ATLF - Alternating-time Temporal Logic](#atl--atlf---alternating-time-temporal-logic)
5.  [NatATL / NatATLF - Natural ATL](#natatl--natatlf---natural-atl)
6.  [NatSL - Natural Strategy Logic](#natsl---natural-strategy-logic)
7.  [OATL - One-sided ATL](#oatl---one-sided-atl)
8.  [OL - One-sided LTL](#ol---one-sided-ltl)
9.  [RBATL / RABATL - Resource-Bounded ATL](#rbatl--rabatl---resource-bounded-atl)
10. [CapATL - Capacity ATL](#capatl---capacity-atl)
11. [COTL - Coalitional Optimal Temporal Logic](#cotl---coalitional-optimal-temporal-logic)
12. [Atomic Proposition Policy](#atomic-proposition-policy)
13. [Model Syntax](#model-syntax)

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
2.  **Operators**: `X` (next), `F` (eventually), `G` (globally/always), `U` (until).
3.  **Propositions**: `[a-z][a-z0-9_]*` (Lowercase start, then alphanumerics/underscores).
4.  **Grouping**: Parentheses `()` and square brackets `[]` are both supported. (Note: `[]` is unique to CTL).

**Validation Rules:**
- **Quantifier Requirement**: In CTL, every temporal operator (X, F, G, U) MUST be preceded by a path quantifier (A or E).
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
| **State Props** | p, q | `[a-z][a-z0-9_]*` |

---

<a id="ltl---linear-temporal-logic"></a>
## LTL - Linear Temporal Logic

### Theoretical Background

LTL is a linear-time logic evaluated over single infinite paths (sequences of states). Unlike CTL, there are no path quantifiers.

**Standard Syntax:**
- **Temporal Operators:**
    - `X`: Next state
    - `F`: Eventually
    - `G`: Globally
    - `U`: Until
    - `R`: Release (Dual of Until)
    - `W`: Weak Until

**Standard Examples:**
- `G p`: p is always true along the path.
- `F (G p)`: p eventually becomes true and stays true forever.
- `G (request -> F grant)`: Every request is eventually followed by a grant.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/LTL/parser.py`

**Supported Syntax:**
1.  **Operators**: `X`, `F`, `G`, `U`, `R`, `W` (and their keyword aliases).
2.  **Propositions**: `[a-z][a-z0-9_]*`.
3.  **No Quantifiers**: Path quantifiers (A/E) are NOT allowed in LTL formulas in VITAMIN.

**Validation Rules:**
- LTL formulas are checked for linear temporal structure.
- Propositions must follow the standard lowercase identifier pattern.

**Formula Examples:**
```text
G p
F (p && G q)
p U q
G (request -> (request R grant))
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Path Quantifiers**| None | None (Strictly enforced) |
| **Temporal Ops** | X, F, G, U, R, W | `X`, `F`, `G`, `U`, `R`, `W` |
| **Boolean Ops** | AND, OR, NOT, IMPLIES | `&&`, `\|\|`, `!`, `->` |
| **Release/Weak** | Supported | Fully Supported |

---

<a id="atl--atlf---alternating-time-temporal-logic"></a>
## ATL / ATLF - Alternating-time Temporal Logic

### Theoretical Background

ATL extends CTL with coalition operators `[A]` (in VITAMIN written as `<A>`) to reason about the capabilities of agents. It is evaluated over Concurrent Game Structures (CGS).

**Standard Syntax:**
- **Coalition Operators:**
    - `<{1,2}> p`: Coalition of agents 1 and 2 has a strategy to ensure p.
    - `<{ }> p`: The empty coalition (equivalent to CTL quantifier `A`).
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
3.  **Propositions**: `[a-z][a-z0-9_]*`.
4.  **Validation**: Agent indices must be in range `[1, n_agent]`.

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
| **Propositions** | p, q | `[a-z][a-z0-9_]*` |
| **Valuation** | Binary (ATL) / [0,1] (ATLF) | Handled by model checker |

---

<a id="natatl--natatlf---natural-atl"></a>
## NatATL / NatATLF - Natural ATL

### Theoretical Background

NatATL extends ATL with explicit capacity constraints on coalitions, allowing reasoning about how many agents from a set are needed to achieve a goal. The **NatATLF** variant uses a specific fixed-point verification pipeline to solve these constraints.

**Standard Syntax:**
- **Capacity Operator**: `<{A}, k> p`
    - `A`: A set of agents.
    - `k`: A positive integer bound on how many agents from `A` can act.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/NatATL/parser.py`

**Supported Syntax:**
1.  **Canonical Form**: `<{1,2}, 3>` (Angle brackets, curly braces for agent set, comma, then positive integer bound).
2.  **Operators**: `X`, `F`, `G`, `U`.
3.  **Propositions**: `[a-z][a-z0-9_]*`.

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
| **Bound k** | Positive integer | Mandatory integer |
| **Temporal Ops** | X, F, G, U | `X`, `F`, `G`, `U` |
| **Propositions** | p, q | `[a-z][a-z0-9_]*` |

### Memory Models and Variants

The behavior of agents in NatATL depends on the **Memory Model** selected during verification. These variants use the same syntax but different underlying algorithms in the VITAMIN engine:

1.  **NatATL Memoryless (Standard)**:
    - Agents act based only on the current state.
    - This matches the standard strategic reasoning of vanilla ATL and is typically the default behavior.
2.  **NatATL Recall**:
    - Agents can remember the full history of the path taken.
    - History-dependent strategies are often essential for satisfying complex capacity constraints that apply over multiple steps.
3.  **NatATL Recall Filter**:
    - A performance-optimized version of the Recall variant.
    - It uses a standard ATL check (which is much faster) as a **pre-filter**. If the property cannot be achieved even without capacity bounds, the system skips the more expensive NatATL Recall verification.

---

<a id="natsl---natural-strategy-logic"></a>
## NatSL - Natural Strategy Logic

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
- **Flexible Identifiers**: Variables (e.g., `x`, `y`, `strat1`) and Propositions (e.g., `p`, `win`, `state_a`) now support any alphanumeric name starting with a letter or underscore: `[A-Za-z_][A-Za-z0-9_]*`.
- **Temporal Constraint**: In current versions, the temporal expression is limited to `F` (Eventually) or `!F` (Not Eventually).

    > [!NOTE]
    > **Why the restriction?** NatSL is currently implemented by reducing formulas to **NatATL**. While NatATL supports `G` (Globally) and `X` (Next), the NatSL engine is optimized for reachability properties.
    >
    > **Extensibility**:
    > - Support for **`G`** and **`X`** can be added in future versions as they map directly to single NatATL operators.
    > - Full **LTL** (nested operators like `G(p -> F q)`) is NOT currently planned for NatSL due to the extreme computational complexity (P-SPACE) and the memory-intensive nature of strategy logic verification. For complex temporal requirements, use the standard **LTL** or **CTL** logic types.


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
| **Propositions**| Any identifier | `[A-Za-z_][A-Za-z0-9_]*` |
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

<a id="oatl---one-sided-atl"></a>
## OATL - One-sided ATL

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
3.  **Propositions**: `[a-z][a-z0-9_]*`.
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
| **Propositions**| p, q | `[a-z][a-z0-9_]*` |

> [!NOTE]
> **Operator Support (R, W):** While some theoretical papers for OATL/OL define only a minimal set of operators (`X, F, G, U`), the VITAMIN implementation includes **`R` (Release)** and **`W` (Weak Until)** for practical expressivity and duality. This allows users to write more complex properties without manual conversion to negated forms.
>
> **Example:** A property like `<1><5> (p R q)` would otherwise need to be written as `<1><5> !(!p U !q)` or `(<1><5> (q U (p && q)) || <1><5> G q)`, which is significantly less readable.


---

<a id="ol---one-sided-ltl"></a>
## OL - One-sided LTL

### Theoretical Background

OL is the linear-time counterpart to OATL. It evaluates cost-bounded formulas over linear paths.

**Standard Syntax:**
- **Demonic Modality**: `<Jk> p`
    - `k`: A positive integer cost bound.
    - `J`: Indicates a demonic cost prefix in linear time.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/OL/parser.py`

**Supported Syntax:**
1.  **Format**: `<Jk>` (e.g., `<J5>`). Note the mandatory `J` within the angle brackets.
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W`.
3.  **Propositions**: `[a-z][a-z0-9_]*`.

**Validation Rules:**
- **Mandatory 'J'**: OL prefixes MUST include the letter `J` after the opening angle bracket (e.g., `<J10>`). A numeric-only prefix (e.g., `<10>`) is rejected.
- **Bound Requirement**: Every temporal operator must be prefixed.

**Formula Examples:**
```text
<J5> F goal
<J10> G ok
<J3> (p U q)
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Cost Prefix (OL)** | <k> | `<Jk>` (Requires 'J') |
| **Coalition (OATL)** | <A><k> | `<A><k>` (Double brackets) |
| **Bound Format** | Positive k | Integer >= 1, no leading zeros |
| **Temporal Ops** | X, F, G, U | X, F, G, U, W, R |

**Key Differences:**
1. **Letter `J` in syntax**: The implementation requires `J` inside the angle brackets so the lexer can distinguish OL prefixes from other `<...>` uses.
2. **Bound validation**: Same numeric rules as other cost logics (>=1, no leading zeros).

---

## RABATL

### Theoretical Background

**Standard Syntax (Academic Notation):**

RABATL extends ATL with recursive strategies and double bounds:

- **Recursive Coalition**:
  - `<A><B> p`: Coalition A with recursive bound B can achieve p
  - Double bounds for nested strategic reasoning

**Semantics:**
- Recursive strategies allow nested strategic reasoning
- Double bounds control both coalition and recursive depth
- More expressive than standard ATL

**Standard Academic Examples:**
- `<1><2>F p`: Agent 1 with recursive bound 2 can eventually achieve p.
- `<1,2><3>G safe`: Agents 1, 2 with recursive bound 3 can maintain safety.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/RABATL/parser.py`

**Supported Syntax:**

1. **Recursive Coalition:**
   - Format: `<coalition><bound>`
   - Example: `<1><2,2>`, `<1,2><3,3>`
   - **Double angle brackets**: First for coalition, second for recursive bound
   - **Multi-resource bounds use commas**: write vectors as `<2,2>`, not `<2:2>`

2. **Temporal Operators:**
   - `X`, `F`, `G`, `U`, `W`, `R` (same as OATL)

3. **Boolean Operators:**
   - Same as OATL: `&&`, `||`, `!`, `->`

4. **Propositions:**
   - Same as OATL: `[a-z][a-z0-9_]*`

**Formula Examples:**
```
<1><2,2>F p
<1><3,3>G p
<1,2><5,5>F p
<1,2><10,10>p U q
```

**Grammar Structure:**
- Coalition-bound pattern: `<\d+(?:,\d+)*><\d+(?:,\d+)*>`
- Distinction is semantic (model checking), not syntactic

**Validation Rules:**
- Coalition and bound are required
- Multi-resource bounds use commas inside the second bracket

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
|--------|--------|----------------|
| **Syntax** | `<A><B>` | `<A><B>` with comma-separated vectors for multi-resource bounds |
| **Semantics** | Recursive strategies | Handled in model checking |
| **Parser** | Separate syntax | **RABATL** reuses the `RBATLParser` class |

**Key Differences:**
1. **Bound Format**: Multi-resource bounds are written with commas, e.g. `<1><2,2>F p`
2. **Semantic Distinction**: Difference is in model checking semantics relative to RBATL
3. **Model Type**: Requires costCGS model

---

<a id="rbatl--rabatl---resource-bounded-atl"></a>
## RBATL / RABATL - Resource-Bounded ATL

### Theoretical Background

Resource-Bounded ATL (RBATL) and its recursive variant (RABATL) reason about coalitions with multiple resource types, where strategies are constrained by a vector of available resources.

**Standard Syntax:**
- **Vector Bounded Coalition**: `<A><b1, b2, ...> p`
    - `A`: Coalitional agents.
    - `b1, b2, ...`: A vector of bounds for different resources (e.g., energy, time, money).

**Semantics:**
- `<A><b1, ..., bn> p` means coalition `A` has a strategy to ensure `p` such that for every possible outcome, the total consumption of resource `i` does not exceed `bi`.
- **RBATL**: Standard resource-bounded semantics.
- **RABATL**: Introduces recursive strategic reasoning, allowing for nested modalities where the remaining resources are passed to sub-formulas.

### Current Implementation

**Parser Location:** `model_checker/parsers/formulas/RBATL/parser.py` (Used for both variants).

**Supported Syntax:**
1.  **Format**: `<coalition><bound1,bound2,...>` (e.g., `<1><10,5>`).
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W`.
3.  **Multi-Resource Bounds**: Resources MUST be comma-separated within the second set of angle brackets.
4.  **Propositions**: Standard `[a-z][a-z0-9_]*`.

**Formula Examples:**
```text
<1><100,50> F goal
<1,2><10,10,10> G safe
<1><5> (p U q)
<1><2,2> (p R q)
```
### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | <A> | `<1,2>` (Indices) |
| **Vector Bound** | <b1, b2, ...> | `<10,5>` (Comma-separated) |
| **Temporal Ops** | X, F, G, U | `X`, `F`, `G`, `U`, `R`, `W` |
| **Propositions** | p, q | `[a-z][a-z0-9_]*` |

> [!NOTE]
> **Duality & Completeness:** Similarly to OATL, the RBATL implementation supports a full set of temporal operators (`U, R, W, G, X, F`) to ensure syntactic completeness and ease of use for complex resource-bounded specifications.
>
> **Conversion Example:** Without the `R` operator, a standard release property like `<1><10,5> (p R q)` would require the use of its dual: `<1><10,5> !(!p U !q)`.


---


**Validation Rules:**
- **Comma Separation**: Using colons or other separators for resource vectors is not supported in the current grammar.
- **Resource Count**: The number of bounds in the vector should ideally match the resource count in the `costCGS` model.

---

<a id="capatl---capacity-atl"></a>
## CapATL - Capacity ATL

### Theoretical Background

Capacity ATL (CapATL) is designed for models with explicit capacity constraints (`capCGS`), often involving knowledge (capability) and agent-scoped properties.

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
4.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`.

**Validation Rules:**
> [!NOTE]
> **Operator Support (W, R):**
> - **Weak Until (`W`) is currently NOT supported** in the CapATL parser; however, this is a syntactic limitation rather than a semantic one.
> - **Technical Rationale**: CapATL uses a specialized "Pointed Knowledge" solver engine. While `W` is mathematically valid, its direct calculation requires a specific greatest fixpoint handler that is currently being prioritized for a future engine update.
> - **Future Extensibility**: The system is designed to allow future support for `W` and `R` through a "Normalization Phase" that will automatically expand these operators into their core dual forms (e.g., `p W q` into `(p U q) || G p`) before verification.
> - **Current Workaround**: Users can manually express Weak Until properties using the equivalent `(p U q) || G p` syntax.
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
| **Temporal** | Full | `X, F, G, U, R` (`W` excluded) |


---

## Model Syntax

VITAMIN supports three types of model formats, which are automatically detected based on the sections present in the file.

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

**Example Action Format:**
For 2 agents: `AC` means Agent 1 performs action `A` and Agent 2 performs action `C`.

### costCGS (CGS with Costs)
Used for OATL, OL, RBATL, and RABATL.
- **Section**: `Transition_With_Costs`
- **Format**: Same dimensions as the transition matrix. Cells contain cost vectors separated by colons (e.g., `1:2:0` for 3 agents).

### capCGS (CGS with Capacities)
Used for CapATL.
- **Section**: `Capacities` (list of capacity names).
- **Section**: `Capacities_assignment` (mapping matrix: Agents x Capacities).
- **Section**: `Actions_for_capacities` (maps resources directly to actions that consume/replenish them).

---

<a id="cotl---coalitional-optimal-temporal-logic"></a>
## COTL - Coalitional Optimal Temporal Logic

### Theoretical Background

Coalitional Optimal Temporal Logic (COTL) is designed for reasoning about optimal strategies in cost-aware game structures (`costCGS`). While OATL focuses on bound satisfaction, COTL is often used for synthesizing strategies that minimize or maximize resource consumption while achieving a goal.

**Standard Syntax:**
- **Optimal Operator**: `<J><k> phi`
    - `J`: Coalition of agents.
    - `k`: A scalar cost constraint or optimization target.

### Current Implementation

**Parser Location:** `model_checker/algorithms/explicit/COTL/COTL.py` (Reuses the **OATL** parser).

**Supported Syntax:**
1.  **Format**: `<coalition><bound>` (e.g., `<1,2><5>`).
2.  **Temporal Operators**: `X`, `F`, `G`, `U`, `R`, `W`.
3.  **Propositions**: Standard `[a-z][a-z0-9_]*`.

**Formula Examples:**
```text
<1><10> F goal
<1,2><5> (p U q)
<1><2> G safe
```

### Comparison: Theory vs Implementation

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| **Coalition** | <J> | `<1,2>` (Indices) |
| **Cost Bound** | <k> | `<5>` (Integer) |
| **Temporal Ops**| X, F, G, U | `X`, `F`, `G`, `U`, `R`, `W` |
| **Propositions**| p, q | `[a-z][a-z0-9_]*` |

> [!NOTE]
> **Implementation Note**: COTL in VITAMIN currently utilizes the same syntactic parser as **OATL**. The distinction lies in the underlying verification engine's handling of cost-optimal strategy synthesis.

---

<a id="atomic-proposition-policy"></a>
## Atomic Proposition Policy

Atomic identifiers for propositions and variables must avoid clashing with reserved keywords (e.g., `and`, `or`, `exists`, `forall`, `F`, `G`).

**Naming Conventions:**
- **Standard**: `[a-z][a-z0-9_]*`
    - Logic: CTL, LTL, ATL, NatATL, OATL, OL, RBATL, CapATL, COTL.
    - Rule: Lowercase start, then alphanumerics or underscores.
- **Extended (NatSL)**: `[A-Za-z_][A-Za-z0-9_]*`
    - Logic: NatSL.
    - Rule: Can start with uppercase or underscores, and use uppercase/lowercase internally.

---

<a id="summary-logic-comparison-matrix"></a>
## Summary: Logic Comparison Matrix

| Logic | Path Type | Key Operators | Coalitions / Bounds | Model Type |
| :--- | :--- | :--- | :--- | :--- |
| **CTL** | Branching | `AX`, `EF`, `AG`, `E(p U q)` | `A`, `E` (Quantifiers) | CGS |
| **LTL** | Linear | `X`, `F`, `G`, `U`, `R`, `W` | None | CGS |
| **ATL** | Branching | `<A>X`, `<A>F`, `<A>G`, `<A>U` | `<1,2>` | CGS |
| **ATLF** | Branching | `<A>X`, `<A>F`, `<A>G`, `<A>U` | `<1,2>` | CGS (Fixed-point) |
| **NatATL (ML)** | Branching | `<A,k>X`, `<A,k>F`, `<A,k>G`, `<A,k>U` | `<{1,2}, 3>` (Memoryless) | CGS |
| **NatATL (Rec)** | Branching | `<A,k>X`, `<A,k>F`, etc. | `<{1,2}, 3>` (Full Recall) | CGS |
| **NatATLF** | Branching | `<A,k>X`, `<A,k>F`, etc. | `<{1,2}, 3>` | CGS (Fixed-point) |
| **NatSL (Seq)** | Branching | `Ex`, `Ax`, `F`, `!F` | `Ex:{k}x:(x,1)` (Sequential) | CGS |
| **NatSL (Alt)** | Branching | `Ex`, `Ax`, `F`, `!F` | `Ex:{k}x:(x,1)` (Alternated) | CGS |
| **OATL** | Branching | `<A><k>X`, `F`, `G`, `U`, `R`, `W` | `<1,2><5>` (Cost) | costCGS |
| **OL** | Linear | `<Jk>X`, `F`, `G`, `U`, `R`, `W` | `<J5>` (Demonic) | costCGS |
| **RBATL** | Branching | `<A><b1,b2>X`, `F`, `G`, `U`, `R`, `W` | `<1><10,5>` (Vectors) | costCGS |
| **CapATL** | Branching | `<A,k>X`, `F`, `G`, `U`, `R`, `Ki`, `i is p` | `<{1,2}, k>` | capCGS |
| **COTL** | Branching | `<J><k>X`, `F`, `G`, `U`, `R`, `W` | `<1,2><k>` (Optimal) | costCGS |


---

## Technical References

The VITAMIN platform incorporates theoretical foundations from the following textbooks:

-   **Baier, C. & Katoen, J. P. (2008)**. _Principles of Model Checking_. MIT Press.
    -   *Coverage*: Theoretical foundations for CTL and LTL, state-space exploration, and labelling algorithms.
-   **Jamroga, W. (2015)**. _Specification of Multi-Agent Systems_.
    -   *Coverage*: Strategic reasoning, ATL/NatATL foundations, and capacity-constrained logic formalisms.

---

*This document serves as the official Logic Knowledge Base for the VITAMIN Model Checker.*


