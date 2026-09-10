# NatSL scalability experiment

This is the paper-oriented experiment for the restricted bounded NatSL[1G]
prototype. It uses only the **space-efficient alternating** architecture
(`mode="space"`). Both implementations have the same acceptance semantics, but
this mode avoids materialising complete strategy domains and retaining every
failed existentially pruned graph. It therefore has the more robust memory
profile when the number of agents and the strategy bound grow.

## Controlled variables

The default grid varies three independent axes:

- total agents: `2, 3, 4, 5`;
- universal strategy-complexity bound: `k = 1, 2, 3, 4`;
- model scale `(states, atomic propositions)`: `(6,3)`, `(10,5)`, `(14,7)`,
  and `(18,9)`.

Within every point, the following factors are fixed:

- one action for the existential controller;
- two actions for each universal opponent;
- one existential agent and `n-1` universal agents;
- goal `Fgoal`;
- three repetitions and a fixed timeout per repetition.

Every proposition vocabulary contains `phase`, `signal`, and `goal`; larger
scales add deterministically labelled observation propositions. We stop at 18
states and 9 propositions because beyond this point the guard vocabulary, rather
than the transition matrix, dominates and most high-agent/high-k points become
timeout runs. Since states and propositions grow together, this axis must be
reported as **model scale**; it does not isolate the causal effect of states alone.

The first universal player is behaviourally relevant. At `k=1`, it can use only
a constant default rule and every bounded opponent profile eventually reaches
`goal`. At `k>=2`, the conditional strategy `phase -> D; T -> C` can avoid the
goal. Remaining universal players do not affect the transition destination, but
their strategy domains remain universally quantified. The same three-state
behavioural core is embedded in every scale. After the goal state is reached,
execution traverses every additional state and returns to the goal, so larger
instances do not contain unreachable padding. Additional observations enlarge
the guard vocabulary without changing the expected truth boundary. Quantifier
and enumeration order are fixed across every point; the behaviourally relevant
opponent precedes the auxiliary universal agents, exposing the intended
worst-case Cartesian enumeration without changing order between configurations.

## Run

From the repository root:

```bash
python -m pip install -r requirements-natsl-benchmark.txt
python -m experiments.natsl.run
```

A short validation run is:

```bash
python -m experiments.natsl.run --quick \
  --output benchmark_results/natsl_scalability_quick
```

For the paper, use a longer timeout and resume safely if interrupted:

```bash
python -m experiments.natsl.run \
  --agents 2 3 4 5 --bounds 1 2 3 4 \
  --scales 6:3 10:5 14:7 18:9 \
  --repetitions 3 --timeout 120 \
  --output benchmark_results/reproduction_main

python -m experiments.natsl.run \
  --agents 2 3 4 5 --bounds 1 2 3 4 \
  --scales 6:3 10:5 14:7 18:9 \
  --repetitions 3 --timeout 120 \
  --output benchmark_results/reproduction_main --resume
```

The larger-model stress test can be reproduced with:

```bash
python -m experiments.natsl.run \
  --agents 2 3 --bounds 1 2 3 4 \
  --scales 30:15 50:25 100:50 \
  --repetitions 3 --timeout 120 \
  --output benchmark_results/reproduction_large
```

The 120-second threshold keeps the complete three-repetition grid bounded by an
overnight run even when many points explode. A different threshold is valid, but
must be fixed before running and reported in the paper.

The output contains `results.csv`, `summary.csv`, `configuration.json`, all
generated models, and these PNG/PDF figure families:

- `plots_by_k/runtime_k_K`: one explicit graph for every fixed `k`;
- `plots_by_agents/runtime_agents_N`: one graph for every fixed agent count;
- `summary_by_k` and `summary_by_agents`: compact coloured multipanel figures;
- `heatmaps_by_scale/runtime_*`: one runtime heatmap for every model scale;
- `heatmaps_by_scale/strategy_space_*`: syntactic profile-space upper bounds.

The upper bounds are not measured visited-profile counts. Timeouts are written
as `status=timeout` and shown as timeout triangles. Do not replace them with
fabricated runtimes.

## NatATL/ATL clarification

The checker does not translate a mixed NatSL prefix into a NatATL formula. It
reuses VITAMIN's memoryless NatATL pruning and CTL backend. For each already
generated existential natural strategy, it first checks the stronger case in
which opponents are unrestricted; a positive result is a sound shortcut. A
negative result is inconclusive and bounded universal profiles are enumerated.

A global `ATL = false` rejection is not sound for this experiment: failure
against arbitrary opponents does not exclude success against the smaller set of
natural opponent strategies of complexity at most `k`. The benchmark therefore
retains the positive shortcut and does not add a global ATL prefilter.

## Reporting

Report the machine, operating system, Python version, timeout, repetitions and
timeout runs. The `k>=2` negative points may terminate as soon as a
counterstrategy is found, so report `Universal profiles checked` beside runtime.
