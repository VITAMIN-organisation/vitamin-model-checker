# Logistics Robot Example

A larger NatSL model lives in the test fixtures:

`model_checker/tests/fixtures/CGS/NatSL/logistics_robot.txt`

Formula:

```text
E{2}x E{1}z A{1}y: (x, 1)(z, 3)(y, 2) F optimal
```

It complements the minimal regression models by exercising a multi-agent setting
with bounded natural strategies and explicit strategy bindings.

The example is useful for checking:

- multiple agents;
- bounded strategy variables;
- explicit bindings between strategies and agents;
- interaction between existential and universal strategy choices;
- agreement between the `space` and `time` execution modes.

The formula is true in both [modes](../algorithms/natsl.md#modes). In the
result counters ([how a check runs](../algorithms/natsl.md#how-a-check-runs)),
the `space` mode tries 5 existential candidates and the `time` mode 22, and both
check 6 universal profiles. No test uses this model, so the agreement of the two
modes on it is not checked automatically.

## Compact fixture formulas

Other NatSL CGS models in the same fixture folder, used by
`model_checker/tests/integration/algorithms/natsl/test_semantics.py`:

- `restricted_two_agent.txt`
- `bounded_opponent.txt`
- `bounded_controller.txt`

Formulas for those models:

```text
# On restricted_two_agent.txt: true, decided by the unrestricted-opponent
# check (the goal holds whatever agent 2 plays), so no universal profile
# is enumerated.
E{1}x A{1}y: (x, 1)(y, 2) F goal

# On bounded_opponent.txt: true for universal bound 1.
E{1}x A{1}y: (x, 1)(y, 2) F goal

# On bounded_opponent.txt: false for universal bound 2.
E{1}x A{2}y: (x, 1)(y, 2) F goal

# On bounded_controller.txt: false with constant strategies only.
E{1}x: (x, 1) F goal

# On bounded_controller.txt: true with a two-rule strategy.
E{2}x: (x, 1) F goal
```
