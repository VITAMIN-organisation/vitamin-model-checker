# TOL algorithm reference

This page gives the algorithm of the TOL checker in
`model_checker/algorithms/explicit/TOL/` and how it differs from the paper, for a
developer reading or changing the checker. It follows Leneutre, Malvone, and
Ortiz (AAMAS 2025). The logic is introduced in
[TOL in the knowledge base](../reference/logic_knowledge_base.md#tol---timed-obstruction-logic)
and the model file in [timedCGS sections](../reference/file_formats.md#timedcgs-sections),
shared with [TCTL](tctl.md).

## Model

- Type: `timedCGS`, read by `TimedCGS.read_file`; the paper's weighted timed
  automaton (WTA).
- A transition cell is `0` (no edge), an integer (the deactivation cost `W(e)` of
  that edge) or a costCGS-style string with `:` segments, which is summed.
- Costs only price the deactivations of the Demon, the player who removes
  edges (WTA semantics, Definition 5). In the code, delay transitions cost `0`.

## Formula language

Parser: `parsers/formulas/TOL/parser.py`

```text
phi ::= p | ! phi | phi && phi | phi || phi | phi -> phi
      | x <= c | x < c | x >= c | x > c
      | phi : clock_expr | phi with clock_expr
      | j . phi
      | {Jk} F phi | {Jk} G phi | {Jk} X phi
      | {Jk} (phi U psi) | {Jk} (phi R psi) | {Jk} (phi W psi)
```

- `{Jk}` is the demonic prefix, `k` a positive integer. There are no path
  quantifiers `E`/`A`.
- Atoms and clock names start with a lowercase letter (`p`, `safe_1`, `goalA`);
  `Goal` is refused by name and `GOAL` is an `Invalid character` error (see
  [names and keywords](../reference/logic_knowledge_base.md#names-and-keywords)).
  Single-letter uppercase tokens (`F`, `G`, `X`, `U`, `R`, `W`) are temporal
  operators.
- Automaton clocks come from the model's `Clocks` section; formula clocks
  appear in freeze and guards, are disjoint from them, and are added when the
  zone graph `ZG(A, phi)` of model `A` and formula `phi` is built (as in
  [TCTL](tctl.md#model)).
- `{J2} (p U q)` and `{J2} p U q` build the same tree, and so do the forms of
  `R` and `W` (see
  [the knowledge base](../reference/logic_knowledge_base.md#until-after-a-prefix)). A
  connective after a prefix that no parenthesis closes (`{J2}F p && q`,
  `{J2} p U q && r`, freeze `j. p && q`) is a syntax error that gives the
  position and both readings (see
  [the knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

At each step the Demon may deactivate outgoing transitions whose total cost is
at most `k`; the Adversary, the player who moves, then takes a transition that is
still active. `{Jk} theta`, with `theta` the path formula after the prefix,
holds at a state when the Demon has a strategy under which every compatible
path satisfies `theta`. The budget applies to each step.

One step is the obstruction pre-image of Definition 15, for a set of states `Z`
and a budget `n` (the `k` of the prefix); `W(z, sigma, z')` is the cost of the
transition from `z` to `z'` on action `sigma`:

```text
triangle(z, n, Z)    = ( sum of W(z, sigma, z') over transitions z -> z' with z' NOT in Z ) <= n
triangle_down(n, Z)  = { z in Pred(Z) | triangle(z, n, Z) }
```

`Pred(Z)` is the discrete pre-image of `Z`, or the timed one in the zone graph
when a clock guard is attached to the operand, and `Sat(phi)` is the set of
states where `phi` holds. Table 1 gives the computation of each operator:

**Table 1: Fixpoint computation of each TOL operator.**

| Operator | Computation |
| :--- | :--- |
| `{Jk} (phi U psi)` | Least fixpoint: `Y <- psi union (phi intersect triangle_down(k, Y))` (Algorithm 2) |
| `{Jk} (phi R psi)` | Greatest fixpoint: `Y <- psi intersect (phi union triangle_down(k, Y))` (Algorithm 3) |
| `{Jk} F phi` | Least fixpoint: `Y <- phi union triangle_down(k, Y)` |
| `{Jk} G phi` | Greatest fixpoint: `Y <- phi intersect triangle_down(k, Y)` |
| `{Jk} (phi W psi)` | Greatest fixpoint: `Y <- (phi union psi) intersect (psi union triangle_down(k, Y))` |
| `{Jk} X phi` | `triangle_down(k, Sat(phi))` |
| `j . phi` | `Sat(phi)` with formula clock `j` reset to `0` at the current state (Definition 11) |

Implementation techniques for the zone graph and `triangle`: [algorithm design](index.md).

## Theory vs implementation

Table 2 sets the paper next to the code:

**Table 2: TOL theory and implementation.**

| Aspect | Paper (AAMAS 2025) | Code |
| :--- | :--- | :--- |
| Prefix | `<n>`, grade `n >= 0` (Definition 10) | `{Jk}` with `k >= 1`; `{J0}` is a syntax error |
| Primitive operators | `U` and `R` (Definition 10); `F`, `G`, `W` as sugar | `F`, `G`, `W` have their own fixpoints (Table 1), with the same shape as the sugar; the clock guard of `W` is taken from `phi` |
| States | Symbolic states of the zone graph (Algorithm 1, Definition 15) | Sets of location names; `triangle` sums the cost of model edges |
| Next | None: continuous time has no unique next instant | `{Jk} X phi` added as one obstruction step, for parity with the step checks of [OL](ol.md) |
| Freeze | Definition 11 | Written `j.phi` |
| Transition cost | `W(e)` per edge | An integer cell, or a `:`-segmented string whose parts are summed |

## Code map

Table 3 gives the role of each file the TOL checker uses:

**Table 3: TOL code map.**

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

Table 4 lists the TOL tests and fixtures and what each covers:

**Table 4: TOL tests and fixtures.**

| Path | Coverage |
| :--- | :--- |
| `tests/integration/algorithms/tol/test_correctness.py` | Paper `triangle_down` semantics on weighted fixture |
| `tests/fixtures/timedCGS/tctl_tol_minimal.txt` | Shared zero-cost fixture with TCTL |
| `tests/fixtures/timedCGS/tol_cost_2states.txt` | Two-state obstruction-cost fixture |
