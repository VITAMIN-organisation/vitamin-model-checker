# NatSL Semantics

## Ordered strategy quantification

NatSL preserves the ordered quantifier prefix.

For example,

    E{2}xA{1}y:(x,1)(y,2)Fgoal

means that an existential bounded strategy for `x` must succeed against every admissible bounded strategy for `y`.

The current executable fragment supports prefixes of the form `E* A*`, including purely existential prefixes.

## Natural strategies

Natural strategies are represented as ordered condition/action decision lists.

Earlier matching conditions take precedence over later ones, and `T` can be used as a default condition.

The quantifier bound limits strategy complexity.

## Exact action pruning

Applying a strategy removes joint actions that are inconsistent with the selected action for the bound agent.

If the selected action is unavailable in a state covered by the strategy, the strategy profile is inadmissible.

NatSL does not introduce an implicit idle-action fallback.

## Temporal objectives

The current one-goal fragment supports:

- `F p`
- `G p`
- `X p`

and their negated forms.

After strategy pruning, the temporal objective is checked on the resulting CGS through the CTL backend.

## Search modes

The `space` and `time` implementations are different search schedules over the same semantics.

Regression tests check that both modes agree on satisfiability.
