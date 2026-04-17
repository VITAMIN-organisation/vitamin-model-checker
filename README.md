# VITAMIN Model Checker

Core Python package implementing VITAMIN logics, models, and verification routines.

## Prerequisites
- Python 3.10+ with `python3`/`pip` on PATH (CI and Docker use 3.11)
- Make

## Setup (fresh)
1) From the repo root: `cd model-checker`
2) Create and activate a virtualenv (recommended):
   - `python3 -m venv .venv && source .venv/bin/activate`
3) Install in editable mode with benchmark dependency: `make install`

## Run and test

```bash
# Using pytest directly
pytest model_checker/tests/unit/                # Fast unit tests (~5 seconds)
pytest model_checker/tests/integration/         # Integration tests (~6 seconds)
pytest model_checker/tests/                     # All tests (~78 seconds)

# Using Makefile
make test                         # Run tests
make benchmark                    # Run benchmark tool (full matrix)
make benchmark LOGIC=COTL         # Run one logic only
make benchmark OUTPUT=bench.json  # Save pyperf JSON output
make benchmark MODE=compare BASELINE=before.json RESULT=after.json
```

Benchmark documentation lives in a single file:
`model_checker/benchmarking/README.md`.

## Build and maintenance
- Build wheel and sdist into `dist/`: `make build`
- Remove caches: `make clean`
- Format with black (if installed): `make format`
- Lint with ruff (if installed): `make lint`

