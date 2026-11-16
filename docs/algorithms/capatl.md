# CapATL algorithm

The CapATL checker decides `<{A}> phi` on a `capCGS` model, where each agent acts
within one capacity: a named set of actions, taken from the capacities the model
assigns the agent. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#capatl), the model file in
[capCGS sections](../reference/file_formats.md#capcgs-sections), and the steps
shared with other checkers in the [algorithm overview](index.md).

## What `<{A}> phi` means

A complete capacity assignment gives one capacity to each agent. A play is a path
from the current state together with the complete capacity assignments under which
every joint move on it is allowed. The checker follows the semantics of CapATL in
AAMAS 2024 (Def. 2.4, 2.5, 2.9 and 3.2, pp. 125-126):

- The coalition chooses one capacity per member before play and keeps it for the
  whole strategy (Def. 2.5). Every move of a member is in that capacity.
- The opponents may play any capacity the model gives them. A play only counts if
  at least one complete capacity assignment allows it (Def. 2.9), so each opponent
  keeps one capacity along a play, and different plays may use different
  capacities.
- The coalition sees the states and its own moves, not the opponents' moves, and
  may remember the whole history (Def. 2.4, 2.5).
- A formula `<{A}> phi` starts a fresh play at the current state, so its value
  depends only on the state. A strategic operator nested inside `phi` starts its
  own play, and its coalition chooses its capacities again, as the paper allows
  (p. 126). The checker returns the states where the whole formula holds.

On the example model
`model_checker/tests/fixtures/capCGS/CAPATL/capatl_3agents_3states_example.txt`,
`<{1,2}> X g` is false in `q1`: agent 1 must play `A` there, and agent 3, an
opponent, answers agent 2 so that the play goes back to `q0` (`AAB` or `ABA`).
`<{1,2,3}> X g` is true in `q1`: the three agents play `AAA`, with capacity `cap`
for agent 3.

## How a check runs

Because the coalition does not see the opponents' moves, two plays that differ
only in those moves look the same to it, and it must win both with one choice of
moves. The checker therefore builds a game whose node is a state plus the plays
the coalition cannot tell apart that are still undecided, each kept as its set of
allowed assignments. A play is decided once it has met the goal (it is dropped
from the node) or failed it (the coalition loses). A node with no plays left is
won.

For example, on the example model the start node at `q1` holds one play allowing
both assignments (agent 3 with `cap` or `cop`). If the coalition is agents 1 and 2
and plays `AA`, agent 3 can move to `q2` with `A` (only `cap` allows it) or to
`q0` with `B` (only `cop`). The coalition sees which state comes next, so this
gives two nodes, `q2` with one play allowing `cap` and `q0` with one play allowing
`cop`. Two plays end up in one node when they reach the same state through
different opponent moves.

A coalition move at a node leads, for each state the opponents can reach, to the
node holding every play extended by an opponent move that some assignment still
allows. The coalition's next move depends only on the state and these open plays;
nothing else in the history changes what can happen later, so a strategy that
picks one move per node is enough.

For each choice of member capacities, the checker solves this game from the node
(state, one play allowing every assignment). Table 1 lists how each operator is
solved:

**Table 1: CapATL operators.**

| Formula | The coalition wins when | Computed as |
| :--- | :--- | :--- |
| `<{A}> X phi` | some move leads only to `phi` states | the successors of the start node only, no fixpoint |
| `<{A}> phi U psi` | every play reaches `psi` with `phi` before it | least fixpoint over nodes |
| `<{A}> F psi` | as `true U psi` | least fixpoint over nodes |
| `<{A}> phi R psi` | every play keeps `psi` until and including a `phi` state, or forever | greatest fixpoint over nodes |
| `<{A}> G psi` | as `false R psi` | greatest fixpoint over nodes |

A state satisfies `<{A}> phi` when one choice of member capacities wins. `!`,
`&&`, `||` and `->` combine the values of their operands at the same state and,
inside a play, with the same [knowledge](#knowledge-operator).

With $n$ complete capacity assignments and $k$ agents whose knowledge a play keeps
(the agents a `K` names, see [knowledge operator](#knowledge-operator)), a play is
$k+1$ subsets of the assignments, so there are at most
$|S| \cdot 2^{2^{n(k+1)}}$ nodes for $|S|$ states; $k = 0$ without `K`. This bound
is read from the code, not measured. The two example models in
`model_checker/tests/fixtures/capCGS/CAPATL/` have 2 assignments each. The cost on
larger models has not been measured.

The capCGS loader rejects a model whose `Capacities_assignment` does not have one
row per agent and one column per capacity, where an agent has no capacity, or
where an assigned capacity has no line in `Actions_for_capacities`; the message
names the agent or the capacity.

## Difference from the paper's procedure

For formulas without nested strategic operators, the paper decides CapATL by a
reduction to ATEL, ATL with knowledge and imperfect information (Thm 4.5, p. 129).
In the reduced model, an agent may play any action that some capacity still
compatible with the history allows (the move set $d_S$ there). A coalition member
could then use one capacity on one branch and another capacity on a different
branch, which Def. 2.5 does not allow. The checker follows Def. 2.5. The model
`model_checker/tests/fixtures/capCGS/CAPATL/capatl_one_capacity_per_strategy.txt`
separates the two readings: `<{2}> (!lost U goal)` is false at `s0` under
Def. 2.5 and would be true under the reduction.

## How the checker is tested

The tests compare the checker with a brute-force search written from the
definitions (`model_checker/tests/helpers/capatl_reference.py`) on small random
models. The search enumerates paths and strategies up to a depth bound. A play
is decided when it wins, loses, or comes back to a position it has already
passed. A position is the state, with the set of still-possible capacity
assignments for each history the coalition cannot tell apart.

Without `K`, the future of a play depends only on its position, so a play that
returns to one repeats forever: `G` and `R` hold on it and `F` and `U` fail. The
search skips this rule when an operand of the strategic operator contains `K`
outside any nested strategic operator (see [knowledge
operator](#knowledge-operator)), since `K` looks at the whole history.

A play the depth bound cuts, and a nested strategic operator the bound leaves
open, are read once as false and once as true. When both readings agree, the
search returns that answer; otherwise it returns unknown and the tests skip that
state.

## Knowledge operator

`Ka(phi)`, with `a` an agent number and `phi` a capacity formula
([syntax](../reference/logic_knowledge_base.md#capatl)), holds when every complete
capacity assignment agent `a` still considers possible satisfies `phi`
(Def. 3.2, p. 126). An assignment stays possible for `a` while it allows some play
with the same states and the same moves of `a`; `a` does not see the other agents'
moves.

Each play in a game node therefore also keeps, for each agent a `K` names, the
assignments that agent considers possible, and narrows them at each step by the
state reached and the agent's own action. Only `K` reads this knowledge, so the
other agents are left out, which keeps the game smaller. A `K` inside a nested
strategic operator belongs to that operator's own play. Outside any strategic
operator, and at the start of each strategic operator, nothing has been played
yet, so every agent considers every assignment possible. On the example model:

- `K1(1 is c)` holds in every state, because agent 1 has only capacity `c`.
- `K3(3 is cap)` holds nowhere, because agent 3 may have `cop`.
- `<{1,2,3}> X K3(3 is cap)` holds in every state: the coalition can have agent 3
  play `A`, and agent 3 then knows its own capacity is `cap`.
- `<{1,2,3}> X K2(3 is cap)` holds only in `q1`. There, agent 2 playing `A` and
  reaching `q2` means the move was `AAA`, and only `cap` allows that for agent 3.
  From `q0` and `q2` agent 3 may play anything, so agent 2 learns nothing.

The tests for the operands of a strategic operator run per play, with that play's
knowledge, so plays in one node can meet the goal at different steps.
