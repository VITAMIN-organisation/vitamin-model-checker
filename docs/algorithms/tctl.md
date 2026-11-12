# TCTL algorithm reference

This page gives the algorithm of the TCTL checker in
`model_checker/algorithms/explicit/TCTL/` and how it differs from the theory, for
a developer reading or changing the checker. The logic is introduced in
[TCTL in the knowledge base](../reference/logic_knowledge_base.md#tctl---timed-ctl) and the
model file in [timedCGS sections](../reference/file_formats.md#timedcgs-sections). It
follows Hugh Anderson and P.S. Thiagarajan, _Verification of Real-time Systems_,
Chapter 6, "Model checking and timed CTL" (NUS CS5270 lecture notes, also called
the TIGER notes; "the notes" below).

## Model

- Type: `timedCGS`: a CGS with `Clocks`, `Clock_constraints` and `Invariants`
  sections (`TimedCGS.read_file` in
  `parsers/game_structures/timed_cgs/timed_cgs.py`).
- Clocks: the automaton clocks of the `Clocks` section (the set `X` of the
  notes, not the next operator), and `J`, the formula clocks used in freeze and
  guards. `J` is collected from the formula, is disjoint from the automaton
  clocks, and extends the zone graph.

## Formula language

Parser: `parsers/formulas/TCTL/`

```text
phi ::= p | ! phi | phi && phi | phi || phi | phi -> phi
      | x <= c | x < c | x >= c | x > c
      | j . phi                         (freeze)
      | phi : clock_expr                (guard attachment)
      | E F phi | A F phi | E G phi | A G phi
      | E (phi U psi) | A (phi U psi)
      | E phi U psi   | A phi U psi     (same AST as parenthesized form)
```

The words `until`, `eventually` and `globally` stand for `U`, `F` and `G`. `x`
is a clock, `c` an integer constant, and `j` a formula clock, named like a
proposition (lowercase first letter). Freeze `j . phi` resets `j` to 0 and
evaluates `phi`; `phi : clock_expr` attaches a clock guard that filters the
timed backward step.

- No next operator: `X p`, `AX p`, `EX p` and `A next p` are rejected with a
  message that quotes the operator, such as "TCTL has no next operator ('AX' at
  position 1): time is dense, so there is no unique next state". Names such as
  `xray` and `nextstate` are propositions.
- A connective after a prefix that no parenthesis closes (`AF p && q`,
  `A p U q && r`, freeze `j. p && q`, clock constraint `AF p : x<5 && q`) is a
  syntax error that gives the position and both readings (see
  [the knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

The checker builds a zone graph, a symbolic form of the regional transition
system (RTS) whose nodes are regions `(location, zone)` with delay and discrete
edges. Each subformula is evaluated bottom-up into the set of regions that
satisfy it (`rsat` labelling):

- Atoms label all regions at locations where the proposition holds.
- Clock constraints label regions whose zone meets the guard: the zone, the guard
  and the location invariant have a non-empty intersection.
- Freeze `j.phi`: region `r` satisfies `j.phi` when `r` with formula clock `j`
  reset to `0` satisfies `phi`.
- Boolean connectives are union, intersection and complement over all regions.

Temporal operators are fixpoints over region sets. `Pre(Z)` is one reverse step
in the zone graph over delay and discrete edges (`timed_predecessors` in
`parsers/game_structures/timed_cgs/regions.py`), filtered by the attached clock
guard when there is one. `Sat(phi)` is the set of regions labelled with `phi`,
`All` the set of all regions, and `lfp` / `gfp` the least and greatest
fixpoints. Table 1 gives the
fixpoint of each operator:

**Table 1: TCTL temporal operators as fixpoints over regions.**

| Operator | Definition |
| :--- | :--- |
| `EF phi` | `lfp Z . Sat(phi) union Pre(Z)` |
| `AF phi` | `All \ gfp Z . (All \ Sat(phi)) intersect Pre(Z)` |
| `EG phi` | `gfp Z . Sat(phi) intersect Pre(Z)` |
| `AG phi` | `All \ lfp Z . (All \ Sat(phi)) union Pre(Z)` |
| `E(phi U psi)` | `lfp Z . Sat(psi) union (Sat(phi) intersect Pre(Z))` |
| `A(phi U psi)` | `All \ lfp Z . (All \ Sat(psi)) union ((All \ Sat(phi)) intersect (All \ Sat(psi)) intersect AX(Z))` where `AX(Z) = All \ Pre(All \ Z)` |

The result lists the locations where at least one region satisfies the formula.
The initial state satisfies it when the initial node of the zone graph is in the
set or is contained in a satisfying region at the same location.

Implementation techniques for the zone graph: [algorithm design](index.md).

## Theory vs implementation

Table 2 sets the notes next to the code:

**Table 2: TCTL theory and implementation.**

| Aspect | The notes (Definition 35) | Code |
| :--- | :--- | :--- |
| Fragment | `p`, clock constraints, `!`, `&&`, `\|\|`, `z in psi`, `A(psi1 U psi2)`, `E(psi1 U psi2)` | Same, plus `F`, `G`, `->` and attached guards `phi : clock_expr` |
| Freeze | `z in psi` | `j . phi` |
| `F` and `G` | Not in the fragment | Computed directly by the fixpoints of Table 1 |
| Bounded until | Written with freeze, as `z in A((psi1 && z <= 5) U psi2)` | No bounded-until syntax; write the same freeze form |
| Symbolic state space | Regions | Zone graph |

## Code map

Table 3 gives the role of each file the TCTL checker uses:

**Table 3: TCTL code map.**

| Path | Role |
| :--- | :--- |
| `TCTL/TCTL.py` | Entry: parse, extend clocks, zone graph, solve, project |
| `TCTL/solver.py` | AST traversal and handler dispatch |
| `TCTL/evaluators.py` | Leaf, boolean, freeze, and clock-guard handlers |
| `TCTL/operators.py` | Temporal fixpoints on regions |
| `timed_cgs/regions.py` | Region sets, `timed_predecessors`, projection |
| `timed_cgs/formula_clocks.py` | Collect `J` from AST; extend `TimedCGS` |
| `timed_cgs/zone_graph.py` | Zone graph construction |
| `parsers/formulas/TCTL/` | Parser and AST types |

## Tests

Table 4 lists the TCTL tests and fixtures and what each covers:

**Table 4: TCTL tests and fixtures.**

| Path | Coverage |
| :--- | :--- |
| `tests/integration/algorithms/tctl/test_correctness.py` | Temporal ops, guards, freeze |
| `tests/fixtures/timedCGS/tctl_tol_minimal.txt` | Shared timedCGS with TOL |
| `tests/unit/parsers/models/timed_cgs/test_zone_graph.py` | Zone graph paths and guards |
