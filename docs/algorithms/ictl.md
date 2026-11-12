# ICTL algorithm reference

This page gives the algorithm of the ICTL checker in
`model_checker/algorithms/explicit/ICTL/` and how it differs from classical CTL
and the papers, for a developer reading or changing the checker. The logic is
introduced in [ICTL in the knowledge base](../reference/logic_knowledge_base.md#ictl---intuitionistic-ctl)
and the model file in [BirelationalMatrix sections](../reference/file_formats.md#birelationalmatrix-sections-ictl).
The two ICTL papers cited below are AREA23b and EUMAS25b (Bozzelli et al.,
EUMAS 2025), both in `docs/papers/`.

## Model

Type `BirelationalMatrix`: a model `M = <S, P, R, V>` with two relations on one
finite state set `S`, and `V` the labelling of states with atomic propositions
(`AP`). `P` (`<=_P`) is a knowledge preorder, along which
intuitionistic truth is monotone; `R` is the serial transition relation, and
path quantifiers range over infinite `R`-paths.

`check_conditions_hold` in `util/validation.py` rejects a model at load time
unless:

- `P` is reflexive, transitive and antisymmetric, and `R` is serial;
- labelling is monotone: `s <=_P s'` implies `V(s) subseteq V(s')`;
- C1 and C2 of EUMAS25b Definition 1 hold, which Theorem 1 there proves
  necessary and sufficient for ICTL monotonicity (`s -R-> t` means an `R` edge
  from `s` to `t`):

```text
C1: if s <=_P s' and s -R-> t,  then exists t' with s' -R-> t' and t <=_P t'
C2: if s <=_P s' and s' -R-> t', then exists t  with s -R-> t  and t <=_P t'
```

## Formula language

Parser: `parsers/formulas/ICTL/parser.py` (`ICTLParser`, PLY)

```text
phi ::= p | phi && phi | phi || phi | phi -> phi | not phi
      | E X phi | E(phi U psi) | E(phi R psi)
      | A X phi | A(phi U psi) | A(phi R psi)
      | EF phi | EG phi | AF phi | AG phi
```

- Words: `not` or `!`, `->` or `implies`, `and` / `or`, `exist` / `forall`,
  `next`, `until`, `release`, `eventually`, `globally`. A single `&` or `|`,
  and `>` as implication, are errors.
- Atoms match `[a-z][a-zA-Z0-9_]*`; `Goal` is an error (see
  [names and keywords](../reference/logic_knowledge_base.md#names-and-keywords)).
- An Until or Release takes three forms with one tree: `A(p U q)`, `A[p U q]`
  and `A p U q`, and the same with `E` and `R`. A connective after a prefix
  that no parenthesis closes, as in `AX p && q`, is a syntax error (see
  [the knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective)).
- There are no coalition quantifiers.

## Semantic denotations

Each subformula is evaluated bottom-up to a set of states. `Pre_exists(X)` is the
set of R-predecessors of `X`; `Pre_forall(X)` keeps the states whose R-successors
are all in `X`. `s^up = { t | s <=_P t }` is the P-upset of `s`, precomputed by
`get_preorder` in `util/graph.py`, and `X^up = { s | s^up subseteq X }` keeps
the states whose whole upset is in `X`. `^c` is the complement in `S`,
`Pre_op` is `Pre_exists` for `E` and `Pre_forall` for `A`, and `T` and `bottom`
are true and false. Table 1 gives each denotation:

**Table 1: ICTL denotations.**

| Formula | Denotation |
| :--- | :--- |
| `p` | `{ s \| p in V(s) }` |
| `phi && psi`, `phi \|\| psi` | intersection, union |
| `phi -> psi` | `([[phi]]^c union [[psi]])^up` |
| `not phi` | `([[phi]]^c)^up` |
| `E X phi`, `A X phi` | `Pre_exists([[phi]])`, `Pre_forall([[phi]])` |
| `E(phi U psi)`, `A(phi U psi)` | least fixpoint of `[[psi]] union ([[phi]] intersect Pre_op(X))` |
| `E(phi R psi)`, `A(phi R psi)` | greatest fixpoint of `[[psi]] intersect ([[phi]] union Pre_op(X))` |
| `EF phi`, `AF phi` | least: grow from `[[phi]]` under `Pre_op` (`E(T U phi)`, `A(T U phi)`) |
| `EG phi`, `AG phi` | greatest: shrink under `Pre_op` intersect `[[phi]]` (`E(bottom R phi)`, `A(bottom R phi)`) |

Implementation techniques (P-upset precompute): [algorithm design](index.md).

## Theory vs implementation

Table 2 sets classical CTL and the papers next to the code:

**Table 2: ICTL theory and implementation.**

| Aspect | Theory | Code |
| :--- | :--- | :--- |
| Negation and implication | Classical CTL: complement | Complement followed by `^up` |
| Upward closure on `AX` | Not applied (EUMAS25b Proposition 5, Figure 7) | Not applied: `^up` only on `->` and `not` |
| `F` / `G` dualities | Classical CTL: `AF phi = S \ EG(not phi)`, an instance of the A/E dualities of `U` and `R` that EUMAS25b Proposition 3 lists as invalid in ICTL | Not used; each of `EF`, `EG`, `AF`, `AG` has its own fixpoint and handler, not rewritten at parse time |
| Until / Release notation | AREA23b: `A(phi U psi)`; EUMAS25b also `A[bottom R ...]` and `A phi1 U phi2` | All three forms accepted, for `U` and `R` |
| Precedence | Not stated in either paper | A connective after an unclosed prefix is a syntax error |
| Frame conditions | EUMAS25b Definition 1: serial `R`, `P` a partial order, monotone labelling, C1 and C2; AREA23b Definition 2: `P` a preorder | The EUMAS25b conditions, at load time, so a `P` that is not antisymmetric is rejected |

## Code map

Table 3 gives the role of each file the ICTL checker uses:

**Table 3: ICTL code map.**

| Path | Role |
| :--- | :--- |
| `ICTL/ICTL.py` | Entry points and result formatting |
| `ICTL/checker.py` | `ICTLModelChecker`, atom resolution, `^up` helper |
| `ICTL/solver.py` | `solve_tree` dispatch |
| `ICTL/operators.py` | Per-operator state-set updates |
| `ICTL/preimage.py` | R-pre-images |
| `ICTL/util/graph.py` | `get_preorder` (P-upset transitive closure) |
| `ICTL/util/validation.py` | `check_conditions_hold` (C1/C2 and frame checks) |
| `shared/graph_relations.py` | `labeled_pairs` used by validation |
| `parsers/game_structures/birelational_matrix/` | Model loader |
| `parsers/formulas/ICTL/` | PLY parser (`ICTLParser`) |

## Tests

Table 4 lists the ICTL tests and what each covers:

**Table 4: ICTL tests.**

| Path | Coverage |
| :--- | :--- |
| `tests/integration/algorithms/ictl/test_correctness.py` | `^up`, `AX` = `Pre_forall`, sugar encodings, Figure 5, fixture semantics on `tests/integration/algorithms/ictl/fixtures/experiment_2x3.txt` |
| `tests/unit/algorithms/ictl/test_frame_validation.py` | Reject non-well-behaved frames (C1/C2, seriality, preorder) |
| `tests/unit/parsers/formulas/` (ICTL cases) | Parser surface syntax |
