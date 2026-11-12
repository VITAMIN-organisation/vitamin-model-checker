# TOL algorithm reference

This page is the algorithm correctness reference for TOL, for a developer reading
or changing its checker: obstruction pre-images, zone-graph evaluation, and the
code path in `model_checker/algorithms/explicit/TOL/`. It follows Leneutre,
Malvone, and Ortiz (AAMAS 2025), adapted to VITAMIN `timedCGS` surface syntax. The
logic is introduced in [TOL in the knowledge base](../logic_knowledge_base.md#tol---timed-obstruction-logic),
and the timed model format is shared with [TCTL](../TCTL/algorithm.md).

## Overview

TOL is a linear timed logic with demonic obstruction prefixes `{Jk}` over
weighted timed models. At each step the Demon (the player who removes edges) may
deactivate outgoing transitions whose total deactivation cost is at most `k`; the
Adversary (the player who then moves) chooses a non-deactivated transition. A
formula holds at a state when the Demon has an `n`-strategy such that every
compatible path satisfies the temporal property.

Table 1 lists the pieces the checker is built from:

**Table 1: Pieces of the TOL checker.**

| Piece | Role |
| :--- | :--- |
| timedCGS / WTA | Locations, weighted edges, automaton clocks (WTA is the weighted timed automaton of the paper) |
| Zone graph `ZG(A, phi)` | Symbolic timed states; built from the model and formula clocks |
| `{Jk}` prefix | Strategic grade `n` (positive integer); VITAMIN syntax for paper `<n>` |
| `triangle` / `triangle_down` | Obstruction predecessor `triangle_down(n, Z)` (Definition 15) |
| TOL AST | `DemonicOp`, `DemonicBinary`, `FreezeExpr`, clock nodes |

There are no path quantifiers `E`/`A`; branching is not part of the syntax.

## timedCGS models

Same file format as TCTL (see [TCTL/algorithm.md](../TCTL/algorithm.md)). TOL uses
`TimedCGS.read_file` and `ZoneGraph`.

Transition cells may be:

- `0`: no edge
- an integer: the deactivation cost `W(e)` on that edge
- a costCGS-style string with `:` segments: summed in `_transition_cost`

Costs label deactivation of edges; they do not constrain discrete behaviour
beyond the obstruction game (WTA semantics, Definition 5).

## Formula language

Parser: `parsers/formulas/TOL/parser.py`.

### Propositional and clocks

```text
phi ::= p | ! phi | phi && phi | phi || phi | phi -> phi
      | x <= c | x < c | x >= c | x > c
      | phi : clock_expr | phi with clock_expr
      | j . phi
```

- Atoms: identifiers that start with a lowercase letter (`p`, `safe_1`, `goalA`);
  `Goal` is refused by name and an all-capital word such as `GOAL` is an
  `Invalid character` error (see the
  [names and keywords](../logic_knowledge_base.md#names-and-keywords)).
  Single-letter uppercase tokens (`F`, `G`, `X`, `U`, `R`, `W`) remain temporal
  operators.
- Clock names: in a formula (`x<=3`, `x.phi`) and in the `Clocks` section of a
  TimedCGS model they follow the same rule as atoms.
- Automaton clocks: `X` in the paper, from the `Clocks` section of the model.
- Formula clocks: `J` in the paper, disjoint from automaton clocks; they appear in
  freeze and guards, and are collected from the AST and added when building
  `ZG(A, phi)`.
- Freeze: `j . phi` evaluates `phi` with formula clock `j` reset to `0` at the
  current state (Definition 11). VITAMIN surface syntax uses a dot: `j.phi`.
- Clock guard: `phi : x<=c` attaches a guard used during timed backward
  reachability (same attachment style as TCTL).

### Demonic temporal operators

Paper grammar uses `<n>(phi U psi)` and `<n>(phi R psi)`. VITAMIN writes `{Jk}`:

```text
phi ::= {Jk} F phi | {Jk} G phi
      | {Jk} (phi U psi) | {Jk} (phi R psi) | {Jk} (phi W psi)
      | {Jk} X phi          (VITAMIN extension, see below)
```

- `{Jk}`: demonic prefix, `k` a positive integer (`{J[1-9]...}`).
- `{J2} (p U q)` is the form of the paper (Definition 10, PDF page 4); `{J2} p U q`
  builds the same tree. The same holds for `R` and `W`. See
  [the knowledge base](../logic_knowledge_base.md#until-after-a-prefix).
- A connective after a prefix that no parenthesis closes (`{J2}F p && q`,
  `{J2} p U q && r`, freeze `j. p && q`) is a syntax error that gives the position
  and both readings (see
  [the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).
  The paper writes a compound body in parentheses, as in
  $\langle 3\rangle F(j \le 3 \land a)$.
- Sugar (paper): `{Jk} F phi := {Jk} (true U phi)`, `{Jk} G phi := {Jk} (false R phi)`,
  `{Jk} (phi W psi) := {Jk} (psi R (phi || psi))`.

### Surface syntax and VITAMIN extensions

Table 2 lists what the surface syntax adds to or restates from the paper:

**Table 2: VITAMIN extensions to the paper grammar.**

| Extension | Semantics |
| :--- | :--- |
| `{Jk} X phi` | One-step obstruction: `triangle_down(k, Sat(phi))` (discrete/timed pre-image of `Sat(phi)`, filtered by `triangle`) |
| `R`, `W` in surface syntax | Paper defines `W` as sugar; `R` is primitive |
| `\|\|`, `->` | Standard boolean derived connectives |

The paper omits `X` because continuous time has no unique next instant; the
extension is kept for tool parity with OL-style step checks under obstruction.

## Obstruction cost (`triangle`)

Definition 15 (paper): for symbolic set `Z`, state `z`, and bound `n`,

```text
triangle(z, n, Z)    = ( sum of W(z, sigma, z') over transitions z -> z' with z' NOT in Z ) <= n
triangle_down(n, Z)  = { z in Pred(Z) | triangle(z, n, Z) }
```

`Pred(Z)` is the timed or discrete pre-image of `Z` (zone-graph backward step when
a clock guard is present on the operand).

Implementation (`preimage.py`):

- `triangle(tcgs, source_idx, bound, inside_indices)` sums deactivation costs of
  edges from `source_idx` to targets outside `inside_indices` (the current set
  `Z`). Returns whether that sum is `<= bound`.
- `triangle_down(tcgs, zone_graph, n, states, constraints)` computes
  `triangle_down(n, Z)` on location names: discrete or timed `Pred(Z)`, then filter
  by `triangle`.

The cost budget `k` is a per-step budget; see
[the knowledge base](../logic_knowledge_base.md#tol---timed-obstruction-logic).

Delay transitions (`d` in `Sigma_delta`) have cost `0` in the matrix; timed
pre-images use the zone graph.

The implementation techniques for the zone graph and obstruction `triangle` are in [algorithm_design.md](../algorithm_design.md).

## Model-checking pipeline

The checker reads the model, parses the formula, collects its clocks and builds the
zone graph before solving:

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#1f5f99", "primaryTextColor": "#ffffff", "primaryBorderColor": "#4a90d9", "lineColor": "#75808f", "tertiaryTextColor": "#75808f", "titleColor": "#75808f", "clusterBkg": "transparent", "clusterBorder": "#75808f", "edgeLabelBackground": "transparent"}}}%%
flowchart LR
    load["TimedCGS.read_file"]
    parse["TOLParser.parse"]
    clocks["collect formula<br/>clocks J from AST"]
    zones["ZoneGraph(tcgs, formula_clocks)"]
    solve["solve_tree"]
    result["model_checking result dict"]

    load --> parse --> clocks --> zones --> solve --> result
```

Entry point: `model_checking(formula, filename)` in `TOL/TOL.py`.
Evaluation: `solve_tree` in `TOL/solver.py`.

### Fixpoint algorithms (paper Algorithms 1-3)

Table 3 gives the computation behind each operator:

**Table 3: Fixpoint computation of each TOL operator.**

| Operator | Computation |
| :--- | :--- |
| `{Jk} (phi U psi)` | Least fixpoint: `Y <- psi union (phi intersect triangle_down(k, Y))` (Algorithm 2) |
| `{Jk} (phi R psi)` | Greatest fixpoint: `Y <- psi intersect (phi union triangle_down(k, Y))` (Algorithm 3) |
| `{Jk} F phi` | `{Jk} (true U phi)` |
| `{Jk} G phi` | `{Jk} (false R phi)` |
| `{Jk} (phi W psi)` | `{Jk} (psi R (phi || psi))` |
| `{Jk} X phi` | `triangle_down(k, Sat(phi))` (extension) |
| `j . phi` | `Sat(phi)` with formula clock `j` in `ZG(A, phi)`; reset at entry (Algorithm 1) |

The AST node types are `AtomicProp`, `Unary`, `Binary`, `DemonicOp`,
`DemonicBinary`, `FreezeExpr`, `ClockExpr` and `SimpleTimeExpr`. The shared timed
helpers are in `parsers/game_structures/timed_cgs/semantics.py`.

## Code map

Table 4 gives the role of each file the TOL checker uses:

**Table 4: TOL code map.**

| Path | Role |
| :--- | :--- |
| `TOL/TOL.py` | Entry, formula-clock setup, `ZoneGraph` construction |
| `TOL/solver.py` | AST traversal and operator dispatch |
| `TOL/operators.py` | Per-operator handlers and fixpoints |
| `TOL/preimage.py` | `triangle`, `triangle_down`, discrete/timed pre-images |
| `timed_cgs/formula_clocks.py` | Collect `J` from AST; extend `clocks_dict` |
| `shared/timed_ast_operators.py` | Shared boolean/leaf handlers for TCTL and TOL |
| `parsers/formulas/TOL/` | Parser and AST types |
| `parsers/game_structures/timed_cgs/` | Model, zones, shared `semantics` |

## Tests

Table 5 lists the TOL tests and fixtures and what each covers:

**Table 5: TOL tests and fixtures.**

| Path | Coverage |
| :--- | :--- |
| `tests/integration/algorithms/tol/test_correctness.py` | Paper `triangle_down` semantics on weighted fixture |
| `tests/fixtures/timedCGS/tctl_tol_minimal.txt` | Shared zero-cost fixture with TCTL |
| `tests/fixtures/timedCGS/tol_cost_2states.txt` | Two-state obstruction-cost fixture |
