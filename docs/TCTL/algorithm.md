# TCTL algorithm reference

This page is the algorithm correctness reference for TCTL, for a developer reading
or changing its checker: zone-graph RTS, `rsat` labelling, freeze/guards, and the
code path in `model_checker/algorithms/explicit/TCTL/`. The logic is introduced in
[TCTL in the knowledge base](../logic_knowledge_base.md#tctl---timed-ctl) and the
model file in [timedCGS sections](../file_formats.md#timedcgs-sections). It follows Hugh Anderson and
P.S. Thiagarajan, _Verification of Real-time Systems_, Chapter 6, "Model
checking and timed CTL" (NUS CS5270 lecture notes; TIGER notes): regional
transition system, TCTL-minus fragment, and the `rsat` labelling algorithm.

## Overview

TCTL is checked over timedCGS models using a zone graph as a symbolic
representation of the regional transition system (RTS). Table 1 lists the pieces
involved:

**Table 1: Pieces of the TCTL checker.**

| Piece | Role |
| :--- | :--- |
| timedCGS | Locations, transitions, automaton clocks `X`, guards, resets, invariants |
| Formula clocks `Y` | Collected from the AST; disjoint from `X`; extend the zone graph |
| Zone graph | Symbolic regions `(location, zone)` with delay and discrete edges |
| `rsat` labelling | Bottom-up evaluation into `satisfying_regions` per subformula |

Path quantifiers are `E` and `A`. Temporal operators are `F`, `G`, and `U`. There is
no `X` operator, as in the three TCTL sources in `docs/papers/`. Alur, Courcoubetis
and Dill (`IC93.pdf`, Information and Computation 1993, p. 10) write "TCTL has no
next-time operator [...] because if time is dense then, by definition, there is no
unique next time". The Alur thesis grammar (`Alur-thesis.pdf`, Definition 5.1,
p. 144) has none, and Anderson and Thiagarajan
(`TCTL-Anderson-Thiagarajan-ch6.pdf`, p. 87) write "there is no EX or AX".

`X p`, `AX p`, `EX p` and `A next p` are rejected with a message that quotes the
operator, such as "TCTL has no next operator ('AX' at position 1): time is dense,
so there is no unique next state". Names such as `xray` and `nextstate` are
propositions.

API results project regions to location names where at least one region
satisfies the formula. Initial-state satisfaction holds when any region at the
initial location is satisfying.

## TCTL-minus syntax (paper)

Clock sets:

- `X`: automaton clocks from the model `Clocks` section,
- `Y`: formula clocks from FREEZE and guards in the property.

```text
phi ::= p | gamma | !phi | phi && psi | phi || psi
      | y.reset(phi)                    (freeze; VITAMIN writes y.phi)
      | A[phi U psi]_gamma | E[phi U psi]_gamma
```

VITAMIN surface syntax:

```text
phi ::= p | ! phi | phi && phi | phi || phi | phi -> phi
      | x <= c | x < c | x >= c | x > c
      | j . phi                         (freeze)
      | phi : clock_expr                (guard attachment, paper subscript gamma)
      | E F phi | A F phi | E G phi | A G phi
      | E (phi U psi) | A (phi U psi)
      | E phi U psi   | A phi U psi     (same AST as parenthesized form)
```

Sugar: `F` / `G` / `U` / `until` / `eventually` / `globally`.

A connective after a prefix that no parenthesis closes (`AF p && q`,
`A p U q && r`, freeze `j. p && q`, clock constraint `AF p : x<5 && q`) is a
syntax error that gives the position and both readings, as in every logic with a
prefix; `AF p`, `AG AF p` and `AG (p -> EF q)` parse (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)). The
TCTL sources state no precedence rule and write a compound body in parentheses:
IC93 p. 10 defines $\exists\Diamond_{\sim c}\varphi$ as
$\exists(true\ U_{\sim c}\ \varphi)$, and Alur's thesis (p. 147) writes
$\forall\Box x.[p \to \forall\Diamond y.(q \land y < x+5)]$.

Standard reductions:

- `EF phi`  ~ `E[true U phi]`
- `AF phi`  ~ `A[true U phi]`
- `EG phi`  ~ `!A[!phi U true]`
- `AG phi`  ~ `!E[!phi U true]`

Bounded until (paper encoding via FREEZE):

```text
A[phi U psi]_<=c  ~  y.reset(phi && A[true U (y<=c && psi)])   with fresh y in Y
```

## Satisfaction and `rsat`

- Atoms label all regions at locations where the proposition holds.
- Clock constraints label regions whose zones satisfy the guard (with invariants).
- FREEZE `y.phi`: region `r` satisfies `y.phi` when `r` with formula clock `y`
  reset to `0` satisfies `phi`.
- Until uses region-level fixpoints with timed backward steps. Because
  formulas are evaluated on each zone-graph node, prefix obligations correspond to
  the paper's `phi@i` requirement along delay and discrete edges.
- Boolean connectives are union, intersection, and complement over all regions in
  the zone graph.

## timedCGS models

Models extend costCGS/CGS with timed sections (`TimedCGS.read_file` in
`parsers/game_structures/timed_cgs/timed_cgs.py`):

```text
Clocks
x y
Clock_constraints
...
Invariants
...
```

Base sections (`Transition`, `Name_State`, `Initial_State`, `Atomic_propositions`,
`Labelling`, `Number_of_agents`) match costCGS/CGS.

Implementation techniques (zone graph): [algorithm_design.md](../algorithm_design.md).

## Model-checking pipeline

The checker parses the formula, reads the model, extends the clocks and builds the
zone graph before solving:

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#1f5f99", "primaryTextColor": "#ffffff", "primaryBorderColor": "#4a90d9", "lineColor": "#75808f", "tertiaryTextColor": "#75808f", "titleColor": "#75808f", "clusterBkg": "transparent", "clusterBorder": "#75808f", "edgeLabelBackground": "transparent"}}}%%
flowchart TB
    parse["TCTLParser.parse"]
    load["TimedCGS.read_file"]
    clocks["collect_formula_clocks<br/>+ extend_timed_cgs_clocks"]
    zones["ZoneGraph(tcgs)"]
    solve["solve_tree (rsat)"]
    project["project_regions_to_locations"]
    result["model_checking result dict"]

    parse --> load --> clocks --> zones --> solve --> project --> result
```

Entry point: `model_checking(formula, filename)` in `TCTL/TCTL.py`.

### Timed backward step `Pre`

All temporal operators share `timed_predecessors` in
`parsers/game_structures/timed_cgs/regions.py`: one reverse step in the zone graph
(delay and discrete edges). An optional clock guard filters predecessor zones.

### Fixpoints (region sets)

Table 2 gives the fixpoint each temporal operator computes over region sets:

**Table 2: Temporal operator fixpoints.**

| Operator | Definition |
| :--- | :--- |
| `EF phi` | `lfp Z . Sat(phi) union Pre(Z)` |
| `AF phi` | `All \ gfp Z . (All \ Sat(phi)) intersect Pre(Z)` |
| `EG phi` | `gfp Z . Sat(phi) intersect Pre(Z)` |
| `AG phi` | `All \ lfp Z . (All \ Sat(phi)) union Pre(Z)` |
| `E(phi U psi)` | `lfp Z . Sat(psi) union (Sat(phi) intersect Pre(Z))` |
| `A(phi U psi)` | `All \ lfp Z . !Sat(psi) union (!Sat(phi) intersect !Sat(psi) intersect AX(Z))` where `AX(Z) = All \ Pre(All \ Z)` |

`All` is the set of all `(location, zone)` nodes in the zone graph.

## Code map

Table 3 gives the role of each file the TCTL checker uses:

**Table 3: TCTL code map.**

| Path | Role |
| :--- | :--- |
| `TCTL/TCTL.py` | Entry: parse, extend clocks, zone graph, solve, project |
| `TCTL/solver.py` | AST traversal and handler dispatch |
| `TCTL/evaluators.py` | Leaf, boolean, FREEZE, and clock-guard handlers |
| `TCTL/operators.py` | Temporal fixpoints on regions |
| `timed_cgs/regions.py` | Region sets, `timed_predecessors`, projection |
| `timed_cgs/formula_clocks.py` | Collect `Y` from AST; extend `TimedCGS` |
| `timed_cgs/zone_graph.py` | Zone graph construction |
| `parsers/formulas/TCTL/` | Parser and AST types |

## Tests

Table 4 lists the TCTL tests and fixtures and what each covers:

**Table 4: TCTL tests and fixtures.**

| Path | Coverage |
| :--- | :--- |
| `tests/integration/algorithms/tctl/test_correctness.py` | Temporal ops, guards, FREEZE |
| `tests/fixtures/timedCGS/tctl_tol_minimal.txt` | Shared timedCGS with TOL |
| `tests/unit/parsers/models/timed_cgs/test_zone_graph.py` | Zone graph paths and guards |
