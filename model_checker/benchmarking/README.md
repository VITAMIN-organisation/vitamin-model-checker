# Benchmark tool for model_checker

This is a standalone performance benchmark tool for the `model_checker` package.
It uses [pyperf](https://pyperf.readthedocs.io/) to measure how long
`model_checking(formula, model_path)` takes across different logics, model sizes, and
formula shapes.

## Requirements

- Python 3.10+
- Package installed in editable mode (`pip install -e ".[bench]"`)

## Quick start

From the `model_checker/` directory:

```bash
# Run the full benchmark matrix
make benchmark

# Run only one logic
make benchmark LOGIC=CTL

# Save results to a file
make benchmark OUTPUT=results.json

# Save results and export plots
make benchmark OUTPUT=results.json EXPORT_PLOTS=plots/

# Compare two saved runs
make benchmark MODE=compare BASELINE=before.json RESULT=after.json
```

Or call the CLI directly from any directory (requires the package to be installed, e.g., via `pip install -e .`):

```bash
model_checker-benchmark --logic CTL --output ctl.json
model_checker-benchmark --logic CTL --output ctl.json --export-plots plots/
model_checker-benchmark --mode compare --baseline before.json --result after.json
```

## Installation

```bash
pip install -e ".[bench]"
```

If you also need dev dependencies:

```bash
pip install -e ".[dev,bench]"
```

If you want built-in plot export:

```bash
pip install -e ".[bench,bench-viz]"
```

## CLI options

| Option | Default | Description |
|--------|---------|-------------|
| `--mode {run,compare}` | `run` | Whether to run benchmarks or compare two saved files |
| `--logic LOGIC` | all | Restrict to one logic (e.g. `CTL`, `NatSL_Sequential`) |
| `--output PATH` | — | Write pyperf JSON output to this file |
| `--baseline PATH` | — | Baseline JSON file for compare mode |
| `--result PATH` | — | Candidate JSON file for compare mode |
| `--export-plots DIR` | — | Export analysis charts from `<output>.summary.json` |

The CLI help output is intentionally simplified to these basic options.

## Makefile benchmark variables

The `make benchmark` target supports these variables:

- `MODE` (`run` or `compare`)
- `LOGIC` (optional single-logic filter)
- `OUTPUT` (optional output file path)
- `EXPORT_PLOTS` (optional plot directory; requires `OUTPUT`)
- `BASELINE` and `RESULT` (required when `MODE=compare`)

## Supported logics

| Logic | Model type | Notes |
|-------|-----------|-------|
| `ATL` | CGS | Alternating-time Temporal Logic, memoryless |
| `ATLF` | CGS | ATL with fixed-point semantics |
| `CapATL` | CapCGS | Capacity ATL |
| `COTL` | costCGS | Coalitional Optimal Temporal Logic |
| `CTL` | CGS | Computation tree logic |
| `LTL` | CGS | Linear temporal logic |
| `NatATL` | NatATL CGS | Natural ATL, memoryless |
| `NatATL_Recall` | NatATL CGS | Natural ATL, recall strategies (heavier) |
| `NatATLF` | NatATL CGS | NatATL with fixed-point semantics |
| `NatSL_Alternated` | NatATL CGS | Strategy logic, alternated semantics |
| `NatSL_Sequential` | NatATL CGS | Strategy logic, sequential semantics |
| `OATL` | costCGS | One-sided ATL |
| `OL` | costCGS | One-sided LTL |
| `RABATL` | costCGS | Resource-aware bounded ATL |
| `RBATL` | costCGS | Resource-bounded ATL |

## Comparing runs (the main use case)

The typical workflow when optimising an algorithm:

```bash
# 1. Capture the baseline before your change
make benchmark LOGIC=CTL OUTPUT=before.json

# 2. Make your code change

# 3. Capture after
make benchmark LOGIC=CTL OUTPUT=after.json

# 4. Compare
make benchmark MODE=compare BASELINE=before.json RESULT=after.json
```

pyperf's `compare_to` command will show you the geometric mean speedup/slowdown and
flag statistically significant changes.

## How to read run output

Default output is compact and quiet: dotted progress while running, then one summary table.

Formula shape tags are heuristic and help group behavior:

- `next-step` for formulas using `X`
- `reachability` for formulas using `F`
- `safety` for formulas using `G`
- `until` for formulas using `U`
- `release` for formulas using `R`
- `other` otherwise

The end-of-run report is a single table with both:

- logic rows (with slowest/noisiest case)
- formula-shape rows (with average runtime and variability)

Column names use plain language:

- `avg_runtime`: average runtime in the group
- `runtime_variability`: relative spread of runtime values (percent)
- `slowest_case_by_mean`: case with highest average runtime
- `highest_variability_case`: case with least stable runtime in that group

When using `--output`, the tool writes:

- `<output>` (pyperf suite data at the exact path you passed)
- `<output>.summary.json` (structured case metrics for future graphing/reporting)

With `--export-plots`, the tool also writes PNG charts to the selected directory:

- runtime by logic at a fixed state count
- runtime scaling by number of states
- runtime variability (CV%) by logic
- runtime by formula-shape bucket (heuristic classification)

If `--output` already exists, the CLI asks whether to overwrite, choose a new
file name, or cancel.

## Stability interpretation guide

Use CV% to understand measurement quality:

- CV < 5%: very stable
- 5% to 10%: acceptable
- > 10%: noisy (rerun recommended)

When noisy:

1. rerun on a quieter system
2. increase run depth (more runs/values/warmups)
3. use `python3 -m pyperf system tune`

## How the code is organized

```
benchmarking/
|-- schemas.py      - BenchmarkCase dataclass
|-- cases.py        - the benchmark matrix (add cases here)
|-- adapters.py     - maps logic names to checker callables and model generators
|-- generators.py   - generates model file content in memory (no fixtures on disk)
|-- runner.py       - pyperf execution and suite comparison
|-- cli.py          - CLI entry point
`-- __main__.py     - enables python -m model_checker.benchmarking
```

When a benchmark runs, the flow is:

1. CLI resolves mode and arguments
2. `cases.py` returns the selected cases
3. `adapters.py` picks the right checker callable and model generator for each case
4. `generators.py` builds model text; `runner.py` writes it to a temp file
5. pyperf calls the checker in a subprocess worker and records timing
6. Results optionally saved as a JSON suite

## Adding a new benchmark case

1. Open `cases.py` and add a `BenchmarkCase` entry in the right logic group.
2. If it's a new logic, add the import path to `_CHECKER_REGISTRY` in `adapters.py`
   and add the logic to one of the model-format sets (`_CGS_LOGICS`, `_NATATL_LOGICS`, etc.).
3. If the logic needs a different model layout, add a generator to `generators.py` and
   wire it into `get_model_content()` in `adapters.py`.
4. Smoke-test it:
   ```bash
   make benchmark LOGIC=<YOUR_LOGIC>
   ```

Keep cases representative: prefer a few meaningful sizes over many near-identical ones.

## Troubleshooting

**`pyperf is required`**

```bash
pip install -e ".[bench]"
```

**`No benchmark cases found for logic: ...`**

Check the spelling - logic names are case-sensitive and must match the benchmark
registry exactly (e.g. `NatSL_Sequential`, not `NatSL`).

**Output is noisy or hard to read**

Default mode already suppresses pyperf warning chatter and prints compact summaries.

**compare mode: file not found**

Both `--baseline` and `--result` must point to JSON files produced by a previous
`--output` run of this tool. Raw pyperf output from other tools won't work.
