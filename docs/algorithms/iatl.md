# IATL algorithm reference

This page gives the algorithm of the IATL checker in
`model_checker/algorithms/explicit/IATL/` and how it differs from classical ATL
and the paper (Bozzelli et al., KR 2025), for a developer reading or changing
the checker. The logic is introduced in
[IATL in the knowledge base](../reference/logic_knowledge_base.md#iatl---intuitionistic-atl)
and the model file in [BCGS sections](../reference/file_formats.md#bcgs-sections-iatl).

## Model

Type `BCGS`: a model `M = <S, P, G, V, k>` where `S` is the finite state set,
`G` the CGS transition matrix of joint action profiles (as `II,AA`), `P` the
knowledge preorder (`<=_P`), a 0/1 matrix in the `Preorder` section, `V` the
labelling of states with atomic propositions, and `k` the number of agents. Intuitionistic truth is monotone
along `P`.

`check_conditions_hold` in `util/validation.py` rejects a model at load time
unless:

- the transition matrix is square, every state has an outgoing transition, each
  diagonal cell holds the idle self-loop (`II,...,II`), and the length of each
  action profile is a multiple of `k`;
- `P` is reflexive, transitive and antisymmetric, and labelling is monotone: `s <=_P s'` implies
  `V(s) subseteq V(s')`;
- for every non-empty coalition, C1 (forward simulation of coalition moves along
  `P`) and C2 (the dual, backward) hold (`_check_well_behaved_c1`,
  `_check_well_behaved_c2`).

## Formula language

Parser: `parsers/formulas/IATL/parser.py` (PLY)

```text
phi ::= p | phi && phi | phi || phi | phi -> phi | ! phi
      | <A> X phi | <A> F phi | <A> G phi | <A>(phi U psi) | <A>(phi R psi)
      | [A] X phi | [A] F phi | [A] G phi | [A](phi U psi) | [A](phi R psi)
```

`<A>` (as `<1>`, `<1,2>`) is the existential coalition: `A` can enforce the
property. `[A]` (as `[1]`) is the universal one: every strategy of `A` satisfies
it. `X`, `F`, `G`, `U`, `R` may be written `next`, `eventually`, `globally`,
`until`, `release`. Coalitions are checked against `Number_of_agents` at parse
time.

## Semantic denotations

Each subformula is evaluated bottom-up to a set of states. The two coalition
pre-images (KR 2025 Proposition 2) are:

- `Pre_d(A, X)`: states where `A` has a joint move such that every opponent
  response stays in `X`;
- `Pre_f(A, X)`: states where every move of `A` has some opponent response in
  `X`.

`X^up = { s | every t with s <=_P t is in X }` keeps the states whose whole
P-upset is in `X`, and `^c` is the complement in `S`. Table 1 gives each
denotation, with `Pre_op` standing for `Pre_d` under `<A>` and `Pre_f` under
`[A]`, and `T` and `bottom` for true and false:

**Table 1: IATL denotations.**

| Formula | Denotation |
| :--- | :--- |
| `p` | `{ s \| p in V(s) }` |
| `phi && psi`, `phi \|\| psi` | intersection, union |
| `phi -> psi` | `([[phi]]^c union [[psi]])^up` |
| `! phi` | `([[phi]]^c)^up` |
| `<A> X phi`, `[A] X phi` | `Pre_d(A, [[phi]])`, `Pre_f(A, [[phi]])` |
| `(phi U psi)` | least fixpoint of `[[psi]] union ([[phi]] intersect Pre_op(A, X))` |
| `(phi R psi)` | greatest fixpoint of `[[psi]] intersect ([[phi]] union Pre_op(A, X))` |
| `F phi` | least fixpoint of `[[phi]] union Pre_op(A, X)` (paper: `(T U phi)`) |
| `G phi` | greatest fixpoint of `[[phi]] intersect Pre_op(A, X)` (paper: `(bottom R phi)`) |

Implementation techniques (P-upset precompute, per-coalition transition cache): [algorithm design](index.md).

## Theory vs implementation

Table 2 sets classical ATL and the paper next to the code:

**Table 2: IATL theory and implementation.**

| Aspect | Theory | Code |
| :--- | :--- | :--- |
| Negation and implication | Classical ATL: complement | Complement followed by `^up` |
| Upward closure on `[A] X` | Not applied (KR 2025 Proposition 2, Figure 4) | Not applied: `^up` only on `->` and `!` |
| Dualities | In ATL, `[A]` is expressible through `<A>`, and `U` through `R`; in IATL neither holds (KR 2025, Section 3) | No complement dualities: each operator has its own fixpoint, following the equivalences of KR 2025 Proposition 3 |
| Satisfiability | `(!<Ag>X p) && (!<Ag>X !p)`, with `Ag` all agents, is unsatisfiable in ATL but holds at `s0` of KR 2025 Figure 2 (Proposition 1) | Reproduced by fixture `iatl_figure2_proposition1.txt` |
| Pre-image | Coalition-masked joint actions | Own `preimage.py`, not shared with ICTL, whose pre-images are plain R-edge predecessors |

## Code map

Table 3 gives the role of each file the IATL checker uses:

**Table 3: IATL code map.**

| Path | Role |
| :--- | :--- |
| `IATL/IATL.py` | Entry point |
| `IATL/checker.py` | `IATLModelChecker`, pre-images, `^up` |
| `IATL/solver.py` | `solve_tree` dispatch |
| `IATL/operators.py` | Operator handlers |
| `IATL/preimage.py` | `Pre_d`, `Pre_f`, transition cache |
| `IATL/util/validation.py` | `check_conditions_hold` |
| `ICTL/util/graph.py` | `get_preorder`, the transitive P-upset (shared with ICTL) |
| `parsers/game_structures/bcgs/` | BCGS model loader |
| `parsers/formulas/IATL/parser.py` | Formula parser |

## Tests

Table 4 lists the IATL tests and fixtures and what each covers:

**Table 4: IATL tests and fixtures.**

| Path | Coverage |
| :--- | :--- |
| `tests/integration/algorithms/iatl/test_correctness.py` | Pinned fixture, `Pre_d`/`Pre_f`, `[A]X` = `Pre_f`, `F`/`G` encodings, excluded-middle countermodel, `^up` on `!` |
| `tests/fixtures/CGS/IATL/iatl_2agents_2states_minimal.txt` | Minimal 2-agent BCGS |
| `tests/fixtures/CGS/IATL/iatl_figure2_proposition1.txt` | IATL allows `(!<A>X p) && (!<A>X !p)` where ATL cannot (undetermined `p`) |
