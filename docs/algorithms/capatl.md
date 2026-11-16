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

On the [example model](../../model_checker/tests/fixtures/capCGS/CAPATL/capatl_3agents_3states_example.txt),
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
`&&`, `||` and `->` are set operations on states.

With $n$ complete capacity assignments, a node holds a set of subsets of them, so
there are at most $|S| \cdot 2^{2^n}$ nodes for $|S|$ states, and each choice of
member capacities is solved separately. The two example models in
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
[`capatl_one_capacity_per_strategy.txt`](../../model_checker/tests/fixtures/capCGS/CAPATL/capatl_one_capacity_per_strategy.txt)
separates the two readings: `<{2}> (!lost U goal)` is false at `s0` under
Def. 2.5 and would be true under the reduction.

## How the checker is tested

The tests compare the checker with a brute-force search written from the
definitions (`model_checker/tests/helpers/capatl_reference.py`) on small random
models. The search enumerates paths and strategies up to a depth bound and
answers only where that bound settles the question.

## Knowledge operator

The parser accepts the [knowledge operator](../reference/logic_knowledge_base.md#capatl)
`Ka(cap)`, but the checker cannot evaluate it. Checking a formula that contains it
anywhere returns an error of type `validation`: "The knowledge operator K1(...) is
parsed but not evaluated by the CapATL solver yet", with the operator's number in
place of `1` (`kcap2(...)` is reported as `K2(...)`).
