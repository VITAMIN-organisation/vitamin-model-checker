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
rules; with a smaller `k` no profile exists and the formula is false (p. 14).

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

`NatATL_Recall` lets an agent decide on the whole history so far (the states
visited since the initial state, the current one last), not only the current
state. It follows natural strategies with recall in AIJ 2019 (section 6.1,
p. 21).

As for memoryless strategies, the user gives only `<{A}, k> phi`; the checker
searches for the rules.

### Patterns

A recall strategy is an ordered list of rules `(pattern, action)`. A pattern is a
sequence of letters joined by `.` (then). A letter is `true` or a condition as in
[Strategies](#strategies) (one that holds in some states but not all), printed in
parentheses when it has a connective, such as `(p && q)`. A letter followed by `*`
may be used zero or more times in a row.

A history matches a pattern when its states satisfy the letters in order, each
starred letter used zero or more times, with no state or letter left over. So `p`
matches only the one-state history of a `p` state, `p . q` matches two-state
histories, and `true* . p` matches every history that ends in a `p` state; that is
how the memoryless rule `(p, a)` is written with recall.

After each step the agent plays the action of the first rule whose pattern
matches the history. The last rule is always `(true*, IDLE)`, which matches every
history, so the agent idles when no other rule matches. A list never repeats a
pattern, since the second copy could never be the first to match.

A rule's action must be available at the last state of every history of the model
that matches its pattern (p. 21), where a history may start in any state, not only
the initial one (p. 9). Availability is read from the `Transition` matrix as in
[Strategies](#strategies). Example (invented): in a chain `s0 -> s1 -> ... -> s5`
where `s0` is labelled `a`, `s1` to `s4` are `b` and `s5` is `f`, the rule
`(a . b* . f, B)` needs `B` at `s5` only, the last state of every history it
matches; it does not need `B` at `s0` to `s4`.

The checker generates only patterns of this form: it has no union of patterns and
no `*` on a group such as `(p . q)*`, which AIJ 2019 also allows. Every pattern it
builds is also one of the paper's, so `True` means that a strategy of size at most
`k` exists, while `False` means that none of this form exists; one with a union or
a starred group might.

### Size

The size of a pattern is its number of symbols (the letter's symbols, each `*` and
each `.`), except that a leading `true* .` is free and `true*` alone counts 1
(p. 21). Strategy and coalition sizes are sums, as in [Strategies](#strategies);
the idle rule counts 1. Table 1 checks this on the attacker's strategy of AIJ 2019
Example 11 (p. 22), on the robot soccer model of the paper's Figure 5 (not shipped
with this repo). There `moved` and `stayed` label the states after the goalkeeper moves
or stays, and `run`, `lob`, `shoot` and `idle` are the attacker's actions.

**Table 1: Sizes of the RoboCup recall strategy.**

| Rule | Size |
| :--- | :---: |
| `(true, run)` | 1 |
| `(true . true, run)` | 3 |
| `(true* . moved . true, lob)` | 3 |
| `(true* . stayed . true, shoot)` | 3 |
| `(true*, idle)` | 1 |
| Strategy | 11 |

### How a recall check runs

A check follows the memoryless steps, except steps 2 and 4:

1. Each member's rules other than the idle rule have total size at most
   `k - |A|`. A rule is dropped when no history matches its pattern or its action
   breaks the availability rule. Instead of step 2, every ordered list of the
   remaining rules within that size, followed by the idle rule, is a strategy.
2. Instead of step 4, a profile is checked on a product model. A product state is
   a model state together with how far each rule's pattern has matched the history
   so far; this is the configuration of the proof of AIJ 2019 Lemma 15 (p. 28).
   Its moves are the model's joint actions in which each member plays the action
   of its first matching rule; a member's action is read at its agent number in
   the joint action, not at its position in the coalition. The product is finite,
   so CTL on it covers histories of every length, whatever the goal. As in step 4,
   a profile that leaves a product state with no move is skipped.

Patterns are tried smallest first and then by text, and actions in sorted order,
so the same profile is found first on every run.

## Result

The result has `Satisfiability`, `Complexity Bound`, `Winning Strategy per agent`
(only when satisfied, one list of rules per member, such as
`[{'condition_action_pairs': [('p', 'a'), ('true', 'IDLE')]}]`), `res`
(`Result: True`) and `initial_state` (`Initial state s0: True`).
`Complexity Bound` is the total size of the profile found, or `k` when none
worked. A recall rule list prints its patterns as text, such as
`[('true* . p', 'A'), ('true*', 'IDLE')]`.
