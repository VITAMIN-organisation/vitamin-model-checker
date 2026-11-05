# COTL - Algorithm Reference

For developers who need to know how COTL is checked in this project. Code is in
`model_checker/algorithms/explicit/COTL/`; the method follows D. Catta, J.
Leneutre, V. Malvone, A. Murano, "Coalition Obstruction Temporal Logic: A New
Obstruction Logic to Reason About Demon Coalitions", IJCAI 2025. Syntax and
examples are in the [knowledge base](../logic_knowledge_base.md#cotl); the model
file format is in
[file_formats.md](../file_formats.md#obstructionmodel-sections-cotl).

## Idea

There are no agents, only a graph of states and the demons (their number is
`Number_of_demons` in the model file) that can disable its edges. `<L><n> theta`
holds at a state when the legion `L`, a set of demons, can pay at most `n` per
step to disable edges so that every resulting path satisfies `theta`, whatever
the other demons do. Only the legion's own actions are paid; the other demons
pay nothing.

Notation: `phi` and `psi` are state formulas and `theta` is a path formula such
as `X phi`. The paper writes the legion `G`; here it is `L`, so it is not
confused with the operator `G`.

## Model

Type `ObstructionModel`, read from the `Number_of_demons`, `Demon_actions` and
`Curses` sections.

- The actions of demon `i` at state `s` are the ones its `Demon_actions` lines
  declare, plus the idle action `*`, which is always available and costs 0.
  Every other action costs an integer >= 1.
- A curse is a joint action, one action per demon, and it disables some of the
  edges leaving `s`. The `Curses` section lists only the curses that disable
  something; a curse it does not list disables nothing.
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

`L` is a set of demon indices (from 1) and may be empty (`<>`); `n >= 0` is the
legion's budget per step. `WX` is weak next. Parentheses around a binary
operator are optional.

## Semantics

At each step the legion picks one action per member, of total cost at most `n`.
The other demons then pick any curse that extends it, and the path moves to a
state in `post(c, s)`. `<L><n> theta` holds when the legion has a strategy under
which every resulting path satisfies `theta`.

## Algorithm

Every subformula is evaluated bottom-up to the set of states where it holds.
The formula holds in the model when the initial state is in the final set.

One step has two operators in `COTL/preimage.py`, for a set of states `S`. A
state is in the operator when some action `f` of `L` with cost `<= n` makes, for
every curse `c` extending `f`:

| Operator | Condition on `post(c, s)` | Used by |
| :--- | :--- | :--- |
| `next_in(S)` | non-empty and inside `S` | `X`, `U`, `F` |
| `next_in_or_stop(S)` | inside `S`; empty allowed | `WX`, `R`, `G`, `W` |

`X` demands a next state; `WX` holds when there is none.

Temporal operators are fixpoints, where `T` ranges over sets of states and `|`,
`&` are union and intersection. Least fixpoints iterate up from the starting
set, greatest ones down from it.

| Formula | Fixpoint |
| :--- | :--- |
| `<L><n> X phi` | `next_in(phi)` |
| `<L><n> WX phi` | `next_in_or_stop(phi)` |
| `<L><n> (phi U psi)` | least `T = psi \| (phi & next_in(T))` |
| `<L><n> (phi R psi)` | greatest `T = psi & (phi \| next_in_or_stop(T))` |
| `<L><n> F phi` | least `T = phi \| next_in(T)` |
| `<L><n> G phi` | greatest `T = phi & next_in_or_stop(T)` |
| `<L><n> (phi W psi)` | greatest `T = (phi \| psi) & (psi \| next_in_or_stop(T))` |

`F`, `G` and `W` are implemented directly. They give the same states as
`true U phi`, `false R phi` and `psi R (phi | psi)`.

`LegionSteps` (in `COTL/preimage.py`) builds, once per legion, the choices at
each state: every action of `L` that some listed curse extends, with its cost
and the successor sets the other demons can leave. All actions that no listed
curse extends leave every edge enabled, so only the cheapest of them is kept.
The work per state follows the number of listed curses, not the number of joint
actions, which grows exponentially with the number of demons.

## Stopping paths

`R`, `G`, `W` and `WX` use `next_in_or_stop`, so they also hold on a path that
stops. `X`, `U` and `F` use `next_in`, so the legion must leave a next state.
The demons outside the legion choose the whole curse at once, so one curse that
disables every edge is enough to make `next_in` fail.

## Example

The attack graph of Sec. 5 of the paper
([cotl_attack_graph_3demons_6states.txt](../../model_checker/tests/fixtures/ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt)):
an attacker walks from `s0` to the target `s2_3`, where `q` holds, and demon `i`
is security team `ST_i`. The paper gives no costs, so every block costs 1 and
the budget is 1.

- `<1,3><1> G !q` is true at `s0`: team 1 blocks the only edge out of `s1` and
  team 3 the one out of `s3`, so every attack path stops before `q`. Of the
  legions on teams 1, 2, 3, only `{1,3}` and `{1,2,3}` make it true.
- `<1><1> X !q` is false at `s3`: demon 3 may cut the only edge out of `s3`.

## Pipeline and code

```text
ObstructionModel.read_file -> COTLParser.parse -> build_resolved_formula_tree
  -> solve_tree (LegionSteps + fixpoints) -> result
```

The parser takes the number of demons as `n_agent`. Paths below are relative to
`model_checker/`.

| Path | Role |
| :--- | :--- |
| `parsers/game_structures/obstruction_model/obstruction_model.py` | Model reader and checks |
| `parsers/formulas/COTL/parser.py` | Formula parser |
| `algorithms/explicit/COTL/COTL.py` | Entry |
| `algorithms/explicit/COTL/solver.py` | Operator dispatch, builds `LegionSteps` |
| `algorithms/explicit/COTL/operators.py` | X, WX, F, G, U, R, W fixpoints |
| `algorithms/explicit/COTL/preimage.py` | `LegionSteps`: `next_in`, `next_in_or_stop` |

## Tests

[test_correctness.py](../../model_checker/tests/integration/algorithms/cotl/test_correctness.py)
covers the attack graph above, stopping paths, `X` against `WX`, demons outside
the legion, the budget, the empty legion, and invalid model files (the error
names the line).
