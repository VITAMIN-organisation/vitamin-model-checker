# VITAMIN Model Checker

`vitamin-model-checker` is the core Python package for VITAMIN model checking.
It contains the formula parsers, model parsers, explicit-state algorithms,
benchmarks, fixtures, and tests used by the wider VITAMIN stack.

This repository does not expose an HTTP service by default. The package is used
directly from Python, by the Workbench application, and as the integration target
for `vitamin-module-integrator`.

## Repository Role

| Project | Role |
|---|---|
| `vitamin-model-checker` | Core Python library and CLI/benchmark tooling. |
| `vitamin-module-integrator` | Validates logic bundles and applies them to this repo. |
| `vitamin-workbench` | User-facing web/API application that calls the model checker. |

For the cross-project view, see `docs/vitamin-stack.md`.

## Setup

Python 3.11 is the recommended development version because CI and Docker use it.
The package metadata defines the supported range in `pyproject.toml`.

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
```

`make install` installs the package in editable mode with benchmark support.
For development-only dependencies, you can also use:

```bash
pip install -e ".[dev,bench,docs]"
```

## Run Tests

```bash
pytest model_checker/tests/unit/
pytest model_checker/tests/integration/
pytest model_checker/tests/

make test          # unit + integration style suite, excluding slow tests
make test-models   # full model_checker/tests suite
```

Test-suite details live in `model_checker/tests/README.md`.

## Build Docs

```bash
pip install -e ".[docs]"
mkdocs serve
mkdocs build --strict
```

The documentation starts at `docs/index.md`.

## Benchmarks

```bash
make benchmark
make benchmark LOGIC=COTL
make benchmark OUTPUT=bench.json
make benchmark MODE=compare BASELINE=before.json RESULT=after.json
```

Benchmark details live in `model_checker/benchmarking/README.md`.

## Docker

Docker is mainly for isolated build/test checks:

```bash
cd docker
make build
make test
```

See `docker/README.md` for the Docker workflow.

## Adding Logic

The recommended path is to package a new logic as a VMI bundle, validate it with
`vitamin-module-integrator`, and let the integrator apply the files and entry
points to this repository.

Manual in-repo changes are still useful for maintainers working directly on the
core package. See `docs/adding_a_new_logic.md` for both workflows.
