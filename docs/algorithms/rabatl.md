# RABATL algorithm

The RABATL checker decides the same formulas as [RBATL](rbatl.md), `<A><b> phi`,
on a `costCGS` model whose costs are split by agent: in each state, each joint
action gives every agent its own cost vector. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#rbatl--rabatl), the model file
in [costCGS sections](../reference/file_formats.md#costcgs-sections).

## Overview

RABATL runs the RBATL bounded [pre-image](index.md#overview) (see
[RBATL](rbatl.md#bounded-pre-image)) and
[operators](rbatl.md#operators) unchanged; only the cost of a joint action
differs.

## Cost of a joint action

For each resource `i`, the cost of a joint action at state `s` is the sum of the
costs that the coalition's members pay for it at `s`. The other agents' costs are
not counted. The joint action is within the bound when that sum is at most `b_i`
for every resource `i` that `b` covers.

So the same joint action can be within the bound for one coalition and not for
another, and RBATL and RABATL can give different sets on models that describe the
same game, one with one cost per joint action and one with costs per agent.

Example: two agents; in `s0` the joint action `AA` leads to `s1`, where `p` holds,
and agent 1 pays 1 for it while agent 2 pays 5; `BB` stays in `s0` and costs both
nothing; `s1` loops, with no cost given, so it never enters a result. Table 1
lists the results:

**Table 1: RABATL results on the example.**

| Formula | Coalition cost of `AA` | Result |
| :--- | :---: | :--- |
| `<1><2> X p` | 1 | `{s0}` |
| `<2><2> X p` | 5 | `{}` |
| `<1,2><2> X p` | 6 | `{}` |
| `<1,2><6> X p` | 6 | `{s0}` |

A joint action with no cost for `s` in the model never counts as within the bound,
as in RBATL.
