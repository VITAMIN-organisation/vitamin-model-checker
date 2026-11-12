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
  cost 2, and a vector such as `1:2:0` costs its sum, 3.

The Demon never disables every edge of a state, so a state with one edge keeps it.
With `n = 0` it can still disable edges of cost 0.

Example: in `s0`, an edge of cost 0 leads to `s1`, where `p` holds, and a
self-loop of cost 5 stays in `s0`. `<J0> G !p` holds at `s0`: the Demon disables
the edge to `s1` for free. `<J0> F p` does not.
