# LTL algorithm

The LTL checker decides an LTL formula such as `F goal` or `p U q` on a `CGS`
model by asking whether the agents together have simple strategies under which
every path satisfies it. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#syntax-cards), the model
file in [CGS sections](../reference/file_formats.md#cgs-sections).

## How a check runs

LTL uses the strategies and the search of [NatATL](natatl.md#strategies), with
these settings and differences:

1. Every agent of the model gets a strategy, and the bound is fixed at `k = 5`:
   sizes `i = 1, ..., 5` are tried, each agent's strategy having size exactly `i`.
2. A profile prunes the model as in NatATL, except that in a state no rule covers
   the agent is not restricted (NatATL makes it idle there).
3. A profile that leaves some state with no transition is not admissible and is
   skipped.
4. The formula is rewritten for CTL by putting `A` before each temporal operator:
   `F p` becomes `AF p` and `p U q` becomes `A(p U q)`. The
   [CTL checker](ctl.md) checks it at the initial state of the pruned model.

The rewrite is built from the parsed formula, so `p U q U r` (which groups to the
right) becomes `A(p U A(q U r))`; it is not an exact translation of LTL into CTL.

Each candidate profile starts from a fresh copy of the model, so condition results
are not shared between candidates (see
[speed-ups](index.md#speed-ups)).

## Result

The result has only `res` (`Result: True` or `Result: False`) and `initial_state`
(`Initial state s0: True`); the size at which a profile worked is not returned.
