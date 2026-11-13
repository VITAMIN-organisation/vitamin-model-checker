# NatATL algorithm

The NatATL checker decides `<{A}, k> phi`: does coalition `A` have natural
strategies (lists of condition-action rules, defined [below](#strategies)), small
enough for the bound `k`, that force `phi`? It runs on a `CGS` model. The logic
name `NatATL` runs memoryless strategies, which look only at the current state;
`NatATL_Recall` runs strategies that look at the history. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#syntax-cards), the model file
in [CGS sections](../reference/file_formats.md#cgs-sections).

## Strategies

The memoryless strategies follow Jamroga, Malvone and Murano, "Natural
strategic ability" (AIJ 2019, section 4.1, pp. 10-13). A strategy of one agent is
an ordered list of rules `(condition, action)` whose last rule is
`(true, action)`. In each state the agent plays the action of the first rule whose
condition holds there. The idle action (`I` or `IDLE`; results print `IDLE`) is an
action like any other.

A rule's action must be available to the agent in every state where that rule is
the first to hold, the last rule included (AIJ 2019, footnote 3, p. 11). An action
is available in a state when it appears in a joint action of that state's line of
the `Transition` matrix; a `*` cell there makes every action the agent plays
anywhere in the model available. Rule lists that break this are not generated.

A condition is a Boolean formula over the model's propositions with `!`, `&&` and
`||`, such as `p && !q`. Its size is its number of symbols without parentheses:
`p` is 1, `!p` is 2, `p && !q` is 4, and `true` is 1 (p. 12). The size of a
strategy is the sum of the sizes of its conditions, and the size of a coalition's
profile (one strategy per member of `A`) is the sum over the members (p. 13). The
bound `k` limits that sum, so a coalition of two needs `k >= 2` for its two `true`
rules; a smaller `k` is a validation error.

Example: in `s0` (labelled `p`) action `a` leads to `s1` (labelled `g`) and `I`
stays; `s1` offers only `I`. `<{1}, 1> F g` is false: `(true, a)` is not a strategy,
since `a` is not available in `s1`, and `(true, I)` never leaves `s0`.
`<{1}, 2> F g` is true with `(p, a); (true, I)`.

## How a check runs

The memoryless check builds the strategies once and then tries profiles:

1. Each member needs at least its `true` rule of size 1, so a condition has size
   at most `k - |A|` and one member's strategy at most `k - |A| + 1`. The checker
   lists the conditions up to that size and keeps the smallest condition for each
   set of states where it holds: two conditions that hold in the same states give
   the same strategies. Conditions that hold nowhere or everywhere are dropped.
2. For each member it lists the strategies up to that size and keeps the smallest
   one for each choice of an action per state. A rule is left out when it is the
   first to hold in no state, or in every state no earlier rule took: there it
   acts like the `true` rule, which is smaller.
3. It tries the [profiles](index.md#overview) by total size, smallest first, and
   stops at the first one that works.
4. A profile prunes the model: in each state, every member keeps only the joint
   actions where it plays its strategy's action there. The other agents are not
   restricted. A `*` cell is never pruned. A profile that leaves a state with no
   move is skipped, as in [LTL](ltl.md): it happens when the members' actions are
   each available but never appear together in one joint action, and the CTL check
   would read that dead end as satisfying `AF`.
5. The formula is rewritten with `A` in place of each coalition, so
   `<{1}, 2> F goal` becomes `AF goal`, and the [CTL checker](ctl.md) checks it at
   the initial state of the pruned model.

## Recall

`NatATL_Recall` keeps an earlier kind of rule list, and the
[Strategies](#strategies) section does not apply to it: there is no `true` rule,
conditions are atoms joined by `and` or patterns over histories, and at step
`i = 1, ..., k` each member's strategy has size exactly `i`. It unfolds the model
into a tree of histories of depth 4 from the initial state. A plain condition
prunes every node whose state satisfies it; a pattern, built with `.` (then) and
`*` (repeat), prunes along one history that matches it. A condition that contains
`!` or `*` adds 1 to the size. A strategy fails when a rule's action is not
available where its condition holds. The pruned tree is turned back into a model
and checked as in step 5 above.

## Result

The result has `Satisfiability`, `Complexity Bound`, `Winning Strategy per agent`
(only when satisfied, one list of rules per member, such as
`[{'condition_action_pairs': [('p', 'a'), ('true', 'IDLE')]}]`), `res`
(`Result: True`) and `initial_state` (`Initial state s0: True`). For `NatATL`,
`Complexity Bound` is the total size of the profile found, or `k` when none
worked; for `NatATL_Recall` it is the size `i` at which a profile worked.
