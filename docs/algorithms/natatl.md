# NatATL algorithm

The NatATL checker decides `<{A}, k> phi`: does coalition `A` have simple
strategies, each of size at most `k`, that force `phi`? It runs on a `CGS` model.
The logic name `NatATL` runs memoryless strategies, which look only at the current
state; `NatATL_Recall` runs strategies that look at the history. Formula syntax
is in the [knowledge base](../reference/logic_knowledge_base.md#syntax-cards), the
model file in [CGS sections](../reference/file_formats.md#cgs-sections).

## Strategies

A strategy of one agent is an ordered list of rules `(condition, action)`; no two
rules of a strategy have the same action. A state follows the first rule whose
condition holds there: a rule applies only to the states no earlier rule covered.

A condition is one atom or atoms joined by `and`, such as `p and q`; the generator
may repeat an atom (`p and p and q`), and a negated form puts `!` on the first
atom (`!p and q`). Its size is its number of words, plus 1 if it contains `!`.
The size of a strategy is the sum of the sizes of its conditions.

## How a check runs

1. For `i = 1, 2, ..., k`, the checker lists, for each member of `A`, the
   strategies of size exactly `i` (each set of rules in one order only), and tries
   the profiles, one strategy per member. It stops at the first profile that works;
   which one is found first can vary between runs.
2. A profile prunes the model. In each state a rule covers, the agent keeps only
   the joint actions where it plays the rule's action or idles (the `IDLE` or `I`
   action). In the states no rule covers, the agent idles. Whether the rule's
   action is available in the state is not checked: if it is not, only idling is
   left. A `*` cell is never pruned.
3. The formula is rewritten with `A` in place of each coalition, so
   `<{1}, 2> F goal` becomes `AF goal`, and the [CTL checker](ctl.md) checks it at
   the initial state of the pruned model.

The condition of each rule is checked once on the model and reused across
profiles (see [speed-ups](index.md#speed-ups)).

## Recall

`NatATL_Recall` unfolds the model into a tree of histories of depth 4 from the
initial state. A condition is either a plain condition, which prunes every node
whose state satisfies it, or a pattern over histories, built with `.` (then) and
`*` (repeat), which prunes along one history that matches it. A condition that
contains `!` or `*` adds 1 to the size. Unlike the memoryless case, a strategy fails when a rule's action is not
available where its condition holds. The pruned tree is turned back into a model
and checked as above.

## Result

The result has `Satisfiability`, `Complexity Bound` (the size `i` at which a
profile worked, or `k` when none did), `Winning Strategy per agent` (only when
satisfied, one list of rules per member, such as
`[{'condition_action_pairs': [('q', 'A')]}]`), `res` (`Result: True`) and
`initial_state` (`Initial state s0: True`).

A profile that leaves a state with no move is not rejected, unlike in
[LTL](ltl.md); the CTL check then treats that state as a dead end. Example: two
agents with actions `A`, `B` (agent 1) and `C`, `D` (agent 2) and no idle action.
`s0` (labelled `p`) goes to `s1` (`q`) or `s2` (no atom), `s1` to `s2` or `s3`,
`s2` to `s3`, and `s3` (`p` and `q`) loops. Every move from `s0` leaves `p`, yet
`<{1,2},1> G p` is true at size 1: the strategy found for agent 1, such as
`(q, A)`, has no rule that covers `s0`, so agent 1 must idle there, which removes
every move of `s0`.
