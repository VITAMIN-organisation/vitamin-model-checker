# NatSL logistics robot

This page is for a user trying NatSL beyond the regression tests: it gives a
model with 3 agents and 4 states, its formula and result, and the formulas of
three smaller test fixtures (1-2 agents, 2-3 states). The formula syntax is in
the [knowledge base](../reference/logic_knowledge_base.md#natsl---natural-strategy-logic);
strategies and their bounds are explained in
[Strategies](../algorithms/natsl.md#strategies).

The model is in the test fixtures:

`model_checker/tests/fixtures/CGS/NatSL/logistics_robot.txt`

Formula:

```text
E{2}x E{1}z A{1}y: (x, 1)(z, 3)(y, 2) F optimal
```

It asks for a strategy `x` of size at most 2 for agent 1 and a strategy `z` of
size at most 1 for agent 3 such that, against every strategy `y` of size at most
1 for agent 2, the play reaches a state labelled `optimal` (a proposition of the
model file). Size at most 1 allows only the final `(T, action)` rule; size at
most 2 adds one condition of size 1, a single proposition `p`.

The formula is true in both [modes](../algorithms/natsl.md#modes), `space` and
`time`. In the result counters
([how a check runs](../algorithms/natsl.md#how-a-check-runs)), the `space` mode
tries 5 existential candidates and the `time` mode 22, and both check 6
universal profiles. No test uses this model, so the agreement of the two modes
on it is not checked automatically.

## Compact fixture formulas

The models of Table 1 are in the same fixture folder and are used by
`model_checker/tests/integration/algorithms/natsl/test_semantics.py`:

**Table 1: Formulas of the compact NatSL fixtures.**

| Model | Formula | Result |
| :--- | :--- | :--- |
| `restricted_two_agent.txt` | `E{1}x A{1}y: (x, 1)(y, 2) F goal` | true, decided by the unrestricted-opponent check (the goal holds whatever agent 2 plays), so no universal profile is enumerated |
| `bounded_opponent.txt` | `E{1}x A{1}y: (x, 1)(y, 2) F goal` | true for universal bound 1 |
| `bounded_opponent.txt` | `E{1}x A{2}y: (x, 1)(y, 2) F goal` | false for universal bound 2 |
| `bounded_controller.txt` | `E{1}x: (x, 1) F goal` | false with constant strategies only |
| `bounded_controller.txt` | `E{2}x: (x, 1) F goal` | true with a two-rule strategy |
