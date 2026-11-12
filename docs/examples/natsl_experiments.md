# NatSL Experiments

Reproducible scalability experiments are available under `experiments/natsl/`.

## Quick smoke run

Run:

    python -m experiments.natsl.run --quick --no-plots \
      --output experiments/natsl/results/smoke

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
- peak RSS memory;
- satisfiability status;
- completed repetitions;
- universal profiles checked;
- raw universal strategy-domain size.

## Published artefacts

A curated recorded run is stored under:

    experiments/natsl/published/scalability/

It contains configuration data, raw CSV results, aggregated summaries, and summary plots.
