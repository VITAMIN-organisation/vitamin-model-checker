# NatSL algorithm

The NatSL checker decides formulas such as
`E{2}x A{1}y: (x, 1)(y, 2) F goal`: is there a strategy `x` of size at most 2 for
agent 1 that reaches `goal` against every strategy `y` of size at most 1 for
agent 2? It runs on a `CGS` model. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#natsl---natural-strategy-logic),
the model file in [CGS sections](../reference/file_formats.md#cgs-sections).

## Fragment covered

The checker covers the fragment of NatSL that Aruta, Malvone and Murano describe
for their tool in "Development of Natural Strategies in Strategic Logics" (SPIRIT
2024, p. 5): "strategies target only a single goal, and quantifiers over
existential and universal agents are not alternated". Here that means one goal
(`F`, `G` or `X` on one proposition, or its negation) and a prefix of existential
quantifiers followed by universal ones, as the
[steps below](#how-a-check-runs) check. The grammar of NatSL[F] in AAMAS 2022
(Def. 2, p. 3) allows quantifiers in any order and builds goals with `X` and `U`;
the checker rejects a `U` goal and any prefix that still has a universal
quantifier before an existential one (after an outer `!( ... )` has swapped `E`
and `A`).

## Strategies

A strategy is an ordered list of rules `(condition, action)` ending with
`(T, action)`, where `T` holds everywhere. A state follows the first rule whose
condition holds there. A condition is one literal (`p` or `!p`), or two or more
literals joined all by `and` or all by `or`. Its size counts symbols, with `!`
counted apart: `p` is 1, `!p` is 2, `p and q` is 3. The conditions of a strategy
for a quantifier `E{k}x` or `A{k}x` have a total size of at most `k - 1`, plus 1
for the final `T`; no condition appears twice.

Binding a strategy to agent `a` keeps, in each state, only the joint actions in
which `a` plays the action its rule selects. If that leaves a state with no
transition, the strategy is not admissible: the action must be available, and
there is no fallback to an idle move.

## How a check runs

1. The model is checked: the bindings cover every agent exactly once, the model
   has no `*` cells, and in each state the joint actions are every combination of
   the agents' local actions. The quantifier prefix (`E{2}x A{1}y` in the
   example) must be existential quantifiers followed by universal ones; an outer
   `!( ... )` swaps every `E` and `A` before this check, so
   `!(A{1}y E{2}x: ...)` is accepted.
2. The goal is rewritten for CTL: `F p` as `AF p`, `G p` as `AG p`, `X p` as
   `AX p`, and the negated goals `!F p` as `AG !p`, `!G p` as `AF !p` and `!X p`
   as `AX !p`.
3. For each profile of existential strategies, the model is pruned by their
   bindings:
   - with no universal quantifier, the goal is checked on the pruned model;
   - otherwise the goal is first checked with the opponents unrestricted, and a
     yes is final; on a no, every profile of universal strategies is applied on
     top, and the goal must hold for all of them.
4. The formula holds if some existential profile succeeds.

The goal is checked by the [CTL checker](ctl.md) on the pruned model, at the
initial state.

## Modes

`space` (the default) generates the strategies one existential profile at a time.
`time` builds every strategy first, keeps the pruned models of the profiles that
fail against unrestricted opponents, and then checks the universal strategies on
those.

## Result

Besides `Satisfiability`, `res` and `initial_state`, the result reports the mode,
the normalized formula, the CTL goal, counters of the profiles checked and skipped,
and the last assignment examined (not necessarily a winning one).
