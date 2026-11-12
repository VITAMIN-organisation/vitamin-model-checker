# COTL algorithm reference

This page covers how COTL is checked in this project, for a developer reading or
changing the checker. Code is in
`model_checker/algorithms/explicit/COTL/`; the method follows D. Catta, J.
Leneutre, V. Malvone, J. Ortiz, "Coalition Obstruction Temporal Logic: A New
Obstruction Logic to Reason About Demon Coalitions", IJCAI 2025. Syntax and
examples are in the [knowledge base](../reference/logic_knowledge_base.md#cotl); the model
file format is in
[file_formats.md](../reference/file_formats.md#obstructionmodel-sections-cotl).

## Model

Type `ObstructionModel`, read from the `Number_of_demons`, `Demon_actions` and
`Curses` sections. There are no agents, only a graph of states and demons that
can disable its edges.

- The actions of demon `i` at state `s` are the ones its `Demon_actions` lines
  declare, plus the idle action `*`, which is always available and costs 0.
  Every other action costs an integer >= 1.
- A curse is a joint action, one action per demon, and it disables some of the
  edges leaving a state `s`. A curse extends a legion action `f` when it agrees
  with `f` on the legion's demons. The `Curses` section lists curses with the
  edges they disable; a curse it does not list disables nothing.
- `post(c, s)` is the set of successors of `s` that curse `c` leaves enabled.

A path may be finite: it stops when every edge out of its last state is
disabled, or when that state has no successor.

## Formula language

Parser: `model_checker/parsers/formulas/COTL/parser.py`

```text
phi ::= p | true | false | !phi | phi && phi | phi || phi | phi -> phi
      | <L><n> X phi | <L><n> WX phi | <L><n> F phi | <L><n> G phi
      | <L><n> (phi U psi) | <L><n> (phi R psi) | <L><n> (phi W psi)
```

`L` is a legion, a set of demon indices (from 1) that may be empty (`<>`);
`n >= 0` is the legion's budget per step. `phi` and `psi` are state formulas,
and `theta` below stands for the path formula after the prefix, such as
`X phi`. `WX` is weak next. Parentheses around a binary operator are optional.

## Semantic denotations

At each step the legion picks one action per member, of total cost at most `n`.
The other demons then pick any curse that extends it, at no cost, and the path
moves to a state in `post(c, s)`. `<L><n> theta` holds when the legion has a
strategy under which every resulting path satisfies `theta`.

Every subformula is evaluated bottom-up to the set of states where it holds, and
the formula holds in the model when the initial state is in the final set. One
step has two operators in `COTL/preimage.py`, for a set of states `S`. A state
is in the operator when some action `f` of `L` with cost `<= n` makes, for every
curse `c` extending `f`, the condition of Table 1 hold.

**Table 1: COTL one-step operators.**

| Operator | Condition on `post(c, s)` | Used by |
| :--- | :--- | :--- |
| `next_in(S)` | non-empty and inside `S` | `X`, `U`, `F` |
| `next_in_or_stop(S)` | inside `S`; empty allowed | `WX`, `R`, `G`, `W` |

So `X`, `U` and `F` need the legion to leave a next state, while `WX`, `R`, `G`
and `W` also hold on a path that stops. The demons outside the legion choose the
whole curse at once, so one curse that disables every edge is enough to make
`next_in` fail. Temporal operators are fixpoints, where `T` ranges over sets of
states and `|`, `&` are union and intersection; least fixpoints iterate up from
the starting set, greatest ones down from it. Table 2 gives the fixpoint of each
operator.

**Table 2: COTL temporal operators as fixpoints.**

| Formula | Fixpoint |
| :--- | :--- |
| `<L><n> X phi` | `next_in(phi)` |
| `<L><n> WX phi` | `next_in_or_stop(phi)` |
| `<L><n> (phi U psi)` | least `T = psi \| (phi & next_in(T))` |
| `<L><n> (phi R psi)` | greatest `T = psi & (phi \| next_in_or_stop(T))` |
| `<L><n> F phi` | least `T = phi \| next_in(T)` |
| `<L><n> G phi` | greatest `T = phi & next_in_or_stop(T)` |
| `<L><n> (phi W psi)` | greatest `T = (phi \| psi) & (psi \| next_in_or_stop(T))` |

For example, on the attack graph of Sec. 5 of the paper
([cotl_attack_graph_3demons_6states.txt](https://github.com/VITAMIN-organisation/vitamin-model-checker/blob/main/model_checker/tests/fixtures/ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt)),
an attacker walks from `s0` to the target `s2_3`, where `q` holds, and demon
`i` is security team `ST_i`. The paper gives no costs, so blocking an edge costs
1 and the budget is 1. `<1,3><1> G !q` is true at `s0`: team 1 blocks the only
edge out of `s1` and team 3 the one out of `s3`, so every attack path stops
before `q`.

`LegionSteps` (in `COTL/preimage.py`) keeps only the cheapest of the legion
actions that no listed curse extends; see
[algorithm design](index.md).

## Theory vs implementation

Table 3 sets the paper next to the code:

**Table 3: COTL theory and implementation.**

| Aspect | Paper (IJCAI 2025) | Code |
| :--- | :--- | :--- |
| Legion name | `G` | `L`, so it is not confused with the operator `G` |
| Temporal operators | `X`, weak next, `U`, `R` (Def. 3) | Also `F`, `G`, `W`, computed directly; they give the same states as `true U phi`, `false R phi` and `psi R (phi \|\| psi)` |
| Paths | Finite or infinite maximal paths (Definition 4); Theorem 1 and Algorithm 1 compute `R` and weak next with a step that needs a non-empty successor set | Follows Definition 4: `R`, `G`, `W` and `WX` use `next_in_or_stop`, so they also hold on a path that stops |
| Idle action | Always available, cost 0 (Def. 1) | Same; other actions cost >= 1 |
| Curses | A function from each state and curse to the disabled edges | The `Curses` section lists curses with the edges they disable; a curse it does not list disables nothing |
| Costs in the example | Not given | Blocking an edge costs 1 in the test fixture |

## Code map

Table 4 lists the files and their role; paths are relative to `model_checker/`.

**Table 4: COTL code map.**

| Path | Role |
| :--- | :--- |
| `parsers/game_structures/obstruction_model/obstruction_model.py` | Model reader and checks |
| `parsers/formulas/COTL/parser.py` | Formula parser; takes the number of demons as `n_agent` |
| `algorithms/explicit/COTL/COTL.py` | Entry |
| `algorithms/explicit/COTL/solver.py` | Operator dispatch, builds `LegionSteps` |
| `algorithms/explicit/COTL/operators.py` | X, WX, F, G, U, R, W fixpoints |
| `algorithms/explicit/COTL/preimage.py` | `LegionSteps`: `next_in`, `next_in_or_stop` |

## Tests

[test_correctness.py](https://github.com/VITAMIN-organisation/vitamin-model-checker/blob/main/model_checker/tests/integration/algorithms/cotl/test_correctness.py)
covers the attack graph above, stopping paths, `X` against `WX`, demons outside
the legion, the budget, the empty legion, and invalid model files (the error
names the line).
