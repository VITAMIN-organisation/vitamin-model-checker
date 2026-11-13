# OL algorithm

The OL checker decides `<Jn> phi` on a `costCGS` model: before each move a Demon,
with a budget of `n` per step, disables edges leaving the current state, and the
formula asks whether it can do so such that every remaining path satisfies `phi`.
Formula syntax is in the [knowledge base](../reference/logic_knowledge_base.md#ol),
the model file in [costCGS sections](../reference/file_formats.md#costcgs-sections).

## How a check runs

OL is [OATL](oatl.md) with the coalition of all agents: `<Jn>` is read as
`<1,...,N><n>`, with `N` the number of agents, and the OATL algorithm runs
unchanged, with the same [Demon pre-image](oatl.md#demon-pre-image) and
[operators](oatl.md#operators). With every agent in the coalition, a coalition
move is one joint action, so the Demon disables single joint actions.

The model can be written in either form:

- `Transition` with `Costs_for_actions`: a cell may list several joint actions
  that reach the same state. Disabling that edge means disabling all of them, so
  it costs the sum of their costs.
- `Transition_With_Costs`: each cell is one edge with its cost; `2` is an edge of
  cost 2, a vector such as `1:2:0` costs its sum, 3, and the cell `0` exactly
  means no edge.

Every edge that has a cost must cost at least 1: in ECAI 2023 "edges are
labeled by positive integers" (p. 2). An edge of cost 0 could be disabled with
a budget of 0, so `<J0>` would no longer match CTL (see below). An edge whose
costs add up to 0 or less (`$0` in `Costs_for_actions`, or a cell such as `0:0`,
`00` or `-1`) is a model error that names the edge.

Every state needs at least one outgoing edge (the paper's relation is serial).
The paper's example handles a state with none by adding a self-loop with a cost
("add a loop-edge on s5 to grant seriality, add a cost for each edge", p. 3).
In the checker, write that self-loop as a positive cost in the state's own row
and column. A `*` cell in `Transition_With_Costs` is an error for OL and OATL;
TOL reads it as a self-loop of cost 0 ([TOL grade 0](tol.md#grade-0)).

The Demon never disables every edge of a state, so a state with one edge keeps it.
With `n = 0` it cannot disable any edge that has a cost. So when every edge has
a cost, a formula whose grades are all 0 (the fragment OL0) holds exactly where
the CTL formula with `A` (on all paths) in place of each `<J0>` holds (ECAI
2023, Theorem 3, p. 5). Edges with no cost are handled as in
[OATL](oatl.md#demon-pre-image).

`Initial_State` is optional for OL: the paper's obstruction model is a tuple
`<S, R, L, C>` with no initial state (ECAI 2023, Def. 2, p. 2), and the answer
is the set of states where the formula holds. Without `Initial_State`, the
[result](index.md#steps-shared-by-the-set-based-checkers) field `initial_state`
is the empty string `""`. With it, the state must be in `Name_State`, and the
field says whether the formula holds there. OATL and the other logics still
need `Initial_State`.
