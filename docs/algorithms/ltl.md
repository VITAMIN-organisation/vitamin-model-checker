# LTL algorithm

The LTL checker decides an LTL formula such as `F goal` or `p U q` on a `CGS`
model by asking whether a coalition (a set of agents, all agents by default) has
simple strategies under which every path satisfies it. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#syntax-cards), the model
file in [CGS sections](../reference/file_formats.md#cgs-sections).

## How a check runs

LTL uses its own rule lists, which differ from the [NatATL](natatl.md#strategies)
strategies. A strategy of one agent is an ordered list of rules
`(condition, action)` with no `true` rule and no two rules with the same action;
a condition is one atom or atoms joined by `and`, each atom possibly negated
(`p and !q`), and its size is its number of words, plus 1 for each `!` (`p` is 1, `!p` is 2,
`p and !q` is 4, `!p and !q` is 5).
Conditions with `or` are not generated, although the original VITAMIN code
generated them: with `or`, `G goal` with `k = 5` on
`ltl_1agent_3states_minimal.txt` (3 states, 3 propositions, false) takes 13 s
instead of 0.1 s (best of 3 runs).

1. Each agent of the coalition gets a strategy, and sizes `i = 1, ..., k` are
   tried, each agent's strategy having size exactly `i`. Agents outside the
   coalition get no rule, so pruning leaves their moves open.
2. A [profile](index.md#overview) prunes the model: in each state a rule covers
   first, the agent keeps the joint actions where it plays the rule's action or
   idles (`I` or `IDLE`). In a state no rule covers, the agent is not restricted.
3. A profile that leaves some state with no transition is not admissible and is
   skipped.
4. The formula is rewritten for CTL by putting `A` before each temporal operator:
   `F p` becomes `AF p` and `p U q` becomes `A(p U q)`. The
   [CTL checker](ctl.md) checks it at the initial state of the pruned model.

The coalition and the bound `k` (here the size of each agent's strategy, unlike
the total over the coalition in [NatATL](natatl.md#strategies)) are inputs of the
check, as in the SureWin problem of the
LTL paper (PAAMS 2025, Algorithm 1, p. 4). The keyword
arguments `agents` (agent numbers between 1 and the number of agents, default
all) and `k` (default 5) of `model_checking` set them:

```python
from model_checker.algorithms.explicit.LTL.LTL import model_checking

model_checking("F goal", "model_checker/tests/fixtures/CGS/LTL/ltl_1agent_3states_minimal.txt", k=3, agents=[1])
```

A `k` that is not an integer of at least 1, an empty coalition, an agent named
twice, or an agent number that is not an integer or is outside that range comes
back as a validation error response whose message names the value.

The rewrite is built from the parsed formula, so `p U q U r` (which groups to the
right) becomes `A(p U A(q U r))`; it is not an exact translation of LTL into CTL.

Each candidate profile starts from a fresh copy of the model, so condition results
are not shared between candidates (see
[speed-ups](index.md#speed-ups)).

## Result

The result has only `res` (`Result: True` or `Result: False`) and `initial_state`
(`Initial state s0: True`); the size at which a profile worked is not returned.
