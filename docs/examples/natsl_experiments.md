# NatSL experiments

This page is for anyone who reruns or extends the NatSL scalability benchmark in
`experiments/natsl/`: how to start a short run, what the benchmark varies and
records, and what the recorded run in the repository contains. The checker it
measures is described in [NatSL algorithm](../algorithms/natsl.md).

## Quick smoke run

Run:

```bash
python -m experiments.natsl.run --quick --no-plots \
  --output experiments/natsl/results/smoke
```

`--quick` shrinks the grid to 2 agents, universal bounds 1-2, one model scale
(6 states, 3 propositions), one repetition and a timeout of at most 60 s
(`experiments/natsl/run.py`), so it checks that the pipeline runs in a short
time. Local runs under `experiments/natsl/results/` are ignored by Git.

## Benchmark parameters

The benchmark can vary:

- the number of agents
- the universal natural-strategy bound
- the model scale (states and atomic propositions)
- the number of repetitions
- the timeout per repetition

The default grid and the factors held fixed are in `experiments/natsl/README.md`.
A point is
one combination of agents, bound and scale, run once per repetition; each
repetition runs in a separate process so that its timeout and peak memory are
recorded on their own.

## Recorded metrics

The benchmark records these fields, among others:

- wall-clock runtime
- peak memory (`peak_rss_mb`): the peak working set from `psutil` on Windows,
  the maximum resident set size (`ru_maxrss`) elsewhere
- satisfiability status
- completed repetitions
- universal profiles checked
- raw universal strategy-domain size

## Published artefacts

A recorded run is stored under:

```text
experiments/natsl/published/scalability/
```

It contains configuration data, raw CSV results, aggregated summaries, and summary plots.

The run settings are in `configuration.json` in that folder: `run_id`
20260902T135103Z, started 2026-09-02 on Windows 11 with Python 3.12.2, the
[`space` mode](../algorithms/natsl.md#modes), 2-5 agents, universal bounds 1-4,
4 model scales (6 to 18 states), 3 repetitions per point and a 120 s timeout for
each repetition. `results.csv` has one row per repetition; 78 of its 192 rows
timed out. The run predates `run.py` in the repository: the script was first
committed on 2026-09-09 and has changed since (it writes the formula with
spaces, for one), so a run with it can produce different values in the same
columns.
