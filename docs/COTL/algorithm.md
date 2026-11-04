# COTL - Algorithm Reference

Scope: semantics and code path for COTL in
`model_checker/algorithms/explicit/COTL/`, following D. Catta, J. Leneutre,
V. Malvone, A. Murano, "Coalition Obstruction Temporal Logic: A New Obstruction
Logic to Reason About Demon Coalitions", IJCAI 2025. Syntax and examples are in
the [knowledge base](../logic_knowledge_base.md#cotl); the model file format is
in [file_formats.md](../file_formats.md#obstructionmodel-sections-cotl).

## Model

Type: `ObstructionModel`. There are no agents. The model is a graph
of states, and k demons can temporarily disable its edges:

- `P(i, s)`: actions of demon `i` at state `s`. The idle action `*` is always
  available and costs 0; every other action costs an integer >= 1.
- A curse is a joint action, one action per demon. In state `s`, a curse
  disables a set of edges leaving `s`. The model file lists only the curses
  that disable something.
- `post(c, s)`: the successors of `s` that curse `c` leaves enabled.

A path may be finite: it stops when every edge out of its last state is
disabled, or when that state has no successor.

## Formula language

Parser: `parsers/formulas/COTL/parser.py`

```text
phi ::= p | true | false | !phi | phi && phi | phi || phi | phi -> phi
      | <G><n> X phi | <G><n> WX phi | <G><n> F phi | <G><n> G phi
      | <G><n> (phi U psi) | <G><n> (phi R psi) | <G><n> (phi W psi)
```

`<G><n>` is the legion modality. `G` is a set of demon indices and may
be empty (`<>`), and `n >= 0` is the legion's budget per step. `WX` is weak
next; the name comes from LTLf tools such as LTLf2DFA. The
parentheses around binary operators are optional.

## Semantics

At each step, the legion `G` picks one action per member, with total cost at
most `n`. The other demons then pick any curse that extends it, and the path
moves to a state in `post(c, s)`. `<G><n> theta` holds when the legion has a
strategy under which every resulting path satisfies `theta`. The demons outside
`G` play against it.

## Algorithm

Two one-step operators, in `COTL/preimage.py`:

| Operator | State `s` is in it when some action `f` of `G` with cost `<= n` makes, for every curse `c` extending `f` | Used by |
| :--- | :--- | :--- |
| `next_in(X)` | `post(c, s)` non-empty and inside `X` | `X`, `U`, `F` |
| `next_in_or_stop(X)` | `post(c, s)` inside `X`, empty allowed | `WX`, `R`, `G`, `W` |

The temporal operators are fixpoints:

| Formula | Fixpoint |
| :--- | :--- |
| `<G><n> X phi` | `next_in(phi)` |
| `<G><n> WX phi` | `next_in_or_stop(phi)` |
| `<G><n> (phi U psi)` | least `T = psi \| (phi & next_in(T))` |
| `<G><n> (phi R psi)` | greatest `T = psi & (phi \| next_in_or_stop(T))` |
| `<G><n> F phi` | `true U phi` |
| `<G><n> G phi` | `false R phi` |
| `<G><n> (phi W psi)` | `psi R (phi \| psi)` |

Here `|` is union and `&` is intersection of state sets.

A curse that the model does not list disables nothing. Every action of `G`
that no listed curse extends therefore leads to all successors, and only the
cheapest one matters; it is found by a best-first search that stops after at
most (number of listed curses + 1) candidates. A step is then linear in the
number of listed curses rather than in the number of joint actions, which grows
exponentially with the number of demons.

## Implementation choices

- A path stops when every edge out of its last state is disabled. `X`, `U`
  and `F` use `next_in`, so the legion must leave at least one next state.
  `WX`, `R`, `G` and `W` use `next_in_or_stop`, so they also hold on a path
  that stops. In the attack graph, `<1,3><1> G !q` holds because team 1
  blocks the only edge out of `s1` and the path stops there.
- `WX` holds when every next state, if any, satisfies `phi`.
- The demons outside the legion choose the whole curse at once. If any curse
  extending the legion's action disables every edge, `next_in` fails. In the
  attack graph, `<1><1> X !q` is false at `s3` because demon 3 may cut the
  only edge out of `s3`.

## Model-checking pipeline

```text
ObstructionModel.read_file -> COTLParser.parse(n_agent = number of demons)
  -> build_resolved_formula_tree -> solve_tree (LegionSteps + fixpoints) -> result
```

Entry: `COTL/COTL.py`.

## Code map

| Path | Role |
| :--- | :--- |
| `parsers/game_structures/obstruction_model/obstruction_model.py` | Model file reader and checks |
| `parsers/formulas/COTL/parser.py` | Formula parser |
| `COTL/COTL.py` | Entry |
| `COTL/solver.py` | Operator dispatch |
| `COTL/operators.py` | X, WX, F, G, U, R, W fixpoints |
| `COTL/preimage.py` | `next_in`, `next_in_or_stop` |

COTL shares no code with OATL beyond the generic formula-tree and fixpoint
helpers.

## Tests

`tests/integration/algorithms/cotl/test_correctness.py`, on the Sec. 5 attack
graph (`fixtures/ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt`)
and small hand-made models:

- The attack is blocked only when teams 1 and 3 cooperate, as the paper states.
- Release and `G` hold on a path that the legion stops.
- `X` needs a successor and `WX` does not.
- Demons outside the legion work against it.
- The budget bounds what the legion pays per step.
- `<><0> X` quantifies over every curse of every demon.
- `U` needs its goal and `W` does not.
- The cheapest unlisted action of the legion.
- Invalid model files fail with a message naming the line.
