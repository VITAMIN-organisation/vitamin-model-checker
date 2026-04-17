# File Formats Guide

This guide covers the file formats used by the VITAMIN model checker for Models and Formulas. It is designed to help you quickly understand the structure, requirements, and syntax for writing valid system models and verification formulas.

---

## 1. Model Files (`.txt`)

Model files define game structures and states. The VITAMIN model checker automatically detects the model type based on the section headers present in your `.txt` file.

### Naming Convention
- **Pattern**: `{model_name}.txt` (e.g., `atl_game.txt`)

### Supported Model Types & Required Sections

#### A. CGS (Concurrent Game Structure)
The foundational model format used for branching and linear time logics like **CTL**, **LTL**, **ATL**, **NatATL**, and **NatSL**.
Sections must appear generally in this order:
1.  **Transition** (Required)
2.  **Unknown_Transition_by** (Optional, for experimental partial models)
3.  **Name_State** (Required)
4.  **Initial_State** (Required)
5.  **Atomic_propositions** (Required)
6.  **Labelling** (Required)
7.  **Number_of_agents** (Required)

#### B. costCGS (CGS with Costs)
An extension of CGS used for resource and cost-aware logics like **OATL**, **OL**, **RBATL**, **RABATL**, and **COTL**.
This file type introduces additional cost headers:
-   **Costs_for_actions** or **Costs_for_actions_split**: Define cost constraints for transitions.
-   **Transition_With_Costs**: If this is used instead of `Transition`, transitions are represented by cost structures directly.

#### C. capCGS (CGS with Capacities)
An extension used specifically for **CapATL** and capability reasoning.
This file type introduces these specific headers:
-   **Capacities**: Defines available resources natively.
-   **Capacities_assignment**: A state-to-capacity assignment matrix.
-   **Actions_for_capacities**: Maps capabilities directly to actions.

### Basic Syntax Example

```text
# Simple 2-agent, 2-state model

Transition
# s0 -> s1 (actions AA), s1 -> s0 (any action)
0 AA
* 0

Name_State
s0 s1

Initial_State
s0

Atomic_propositions
p q

Labelling
# s0 has p, s1 has q
1 0
0 1

Number_of_agents
2
```

### Section Details

#### **Transition**
A square matrix (n x n for n states). It defines valid transitions between states.
-   `0`: No transition.
-   `AC`: Joint action string (e.g., Agent 1 plays `A`, Agent 2 plays `C`). String length must match `Number_of_agents`.
-   `A1,A2`: Comma-separated list for specifying multiple valid joint actions between states.
-   `*`: Wildcard indicating that any action allows this transition.

#### **State Declarations**
-   **Name_State**: Space-separated list of unique state names (e.g., `s0 s1 s2`).
-   **Initial_State**: The starting state. Must match exactly one entry in **Name_State**. The wildcard character `*` is not permitted here.

#### **Labelling**
A binary matrix representing properties (n rows x m propositions).
-   `1`: The proposition holds in this specific state.
-   `0`: The proposition does not hold.

#### **Number_of_agents**
An integer specifying the total number of agents. Note that all section headers in the parser are case-sensitive.

#### **costCGS Specific Details**
- **Costs_for_actions**: Format `<action> <state>$<cost_agent1>:<cost_agent2>...` (e.g., `AA s0$1:5`).
- **Costs_for_actions_split**: Used for multi-resource logic vectors like RBATL. The format uses commas for vectors (e.g., `AA s0$1,2:3,4`).
- **Transition_With_Costs**: Allows you to skip action listing in transitions and directly treat the matrix values as costs. The cells may contain cost vectors separated by colons.

---

## 2. Formula Files (`_formula.txt`)

Formula files define the temporal logic constraints, rules, and properties the model checker investigates against the model structure.

### Naming Convention
- **Pattern**: `{model_name}_formula.txt` (Recommended)
- **Note**: Using this pattern allows VITAMIN to automatically discover and pair formulas with their corresponding models in the User Interface and Example Explorer.

### Internal Structure

Formula files allow you to write multiple formulas in a single file to execute multiple tasks without rewriting files.

1.  **Semicolon Terminators**: Every formula **MUST** be terminated by a semicolon (`;`). A formula can span across multiple lines, provided it is properly terminated by a semicolon.
2.  **Optional Labels**: Formulas can be prefixed with a custom label to easily identify them (e.g., `MainCheck: <1>F p;`). Labels must be valid alphanumeric identifiers starting with a letter or underscore and followed by a colon (`:`).
3.  **Primary Formula**: The very first formula listed in the file is automatically treated as the "primary" check evaluated by default.

### Syntax Example

```text
# Main property to check
MainProp: <1> F win ;

# Additional safety cases (label is optional)
SafetyCheck1: <1,2> G safe ;
AG (request -> AF grant) ;
```

### Logic Syntax Overview

The VITAMIN formula parser supports a broad variety of temporal logics. Ensure your formula matches the logic structure and that the selected model (CGS, costCGS, or capCGS) supports evaluating it.

| Logic | Syntax Example | Meaning | Model Match |
| :--- | :--- | :--- | :--- |
| **ATL** | `<1,2> F p` | Coalition of agents 1 and 2 has a strategy to reach p. | CGS |
| **CTL** | `AG p` / `EF [p]` | On all paths, p is globally true. (Exclusively supports `[]` grouping) | CGS |
| **LTL** | `G (p -> F q)` | Globally, if p, then eventually q. | CGS |
| **NatATL** | `<{1,2}, 5> F p` | Coalition {1,2} has a strategy reaching p within a capacity of 5. | CGS |
| **NatSL** | `Ex : (x, 1) F goal` | Existential strategy `x` bound to agent `1` eventually reaching goal. | CGS |
| **OATL** | `<1,2><10> (p W q)`| Coalition {1,2} can reach the objective keeping cost <= 10. | costCGS |
| **OL** | `<J10> G p`| Cost-bounded execution over linear paths with demonic prefix `J`. | costCGS |
| **RBATL** | `<1><10,5> F p`| Agent 1 reaches p bounded by a multi-resource vector bounds of `<10,5>`. | costCGS |
| **RABATL**| `<1><2,2> F p` | Recursive bounded reasoning for agent 1 with a resource vector `2,2`. | costCGS |
| **COTL** | `<1,2><5> G p` | Optimal strategizing structure limited to a cost of 5. | costCGS |
| **CapATL** | `<{1}, 3> F (K1 p)` | Capability reasoning assessing agent knowledge capabilities. | capCGS |

> **Note**: For boolean logical operators, all formula implementations strictly support standard operators: `!` (NOT), `&&` (AND), `||` (OR), and `->` (IMPLIES), alongside constant primitives `true` and `false`.

### Final Formatting Rules
-   **Multi-line formulas**: Allowed, as long as they conclude with a semicolon (`;`).
-   **Comments**: Allowed anywhere, using standard `#` or `//` conventions.
-   **Variables & Operators**: Avoid naming custom propositions with reserved keywords such as `and`, `or`, `F`, `G`, or `exists`. Proper proposition formats strictly use lowercase names (`[a-z][a-z0-9_]*`), with the exception of `NatSL` which supports variables utilizing mixed casing.
