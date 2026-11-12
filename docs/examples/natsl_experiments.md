# NatSL Experiments

Reproducible scalability experiments are available under `experiments/natsl/`.

## Quick smoke run

Run:

```bash
python -m experiments.natsl.run --quick --no-plots \
  --output experiments/natsl/results/smoke
```

The quick configuration is intended for integration checking rather than publication.

Local runs under `experiments/natsl/results/` are ignored by Git.

## Benchmark parameters

The benchmark can vary:

- number of agents;
- universal natural-strategy bound;
- model scale;
- number of atomic propositions;
- number of repetitions;
- per-point timeout.

Each point is executed in a separate process so that timeouts and peak-memory measurements can be recorded independently.

## Recorded metrics

The benchmark records, among other fields:

- wall-clock runtime;
- peak memory (`peak_rss_mb`): the peak working set from `psutil` on Windows,
  the maximum resident set size (`ru_maxrss`) elsewhere;
- satisfiability status;
- completed repetitions;
- universal profiles checked;
- raw universal strategy-domain size.

## Published artefacts

A curated recorded run is stored under:

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
