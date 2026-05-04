# Contributing

Use this page when changing `vitamin-model-checker` itself. If you are adding a
logic as a bundle, start with [Adding a New Logic](adding_a_new_logic.md) and
use `vitamin-module-integrator` first.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,bench,docs]"
```

`make install` is also available, but the explicit `pip install` command is
useful when you need docs and dev dependencies at the same time.

## Test Commands

```bash
pytest model_checker/tests/unit/
pytest model_checker/tests/integration/
pytest model_checker/tests/e2e/
pytest model_checker/tests/

make test
make test-models
```

Use the smallest test scope that proves the change, then run the broader suite
before opening a PR.

## Docs Commands

```bash
mkdocs serve
mkdocs build --strict
```

When changing docs, check links and keep Mermaid diagrams theme-friendly. Do not
add direct colors with `classDef`, `style`, or `themeVariables`.

## Benchmark Commands

```bash
make benchmark LOGIC=CTL
make benchmark LOGIC=CTL OUTPUT=before.json
make benchmark MODE=compare BASELINE=before.json RESULT=after.json
```

Benchmarks are useful when an algorithm change might affect runtime. They do not
replace correctness tests.

## When To Update VMI Or Workbench

- Update VMI docs/code when the bundle format, validation contract, or
  integration behavior changes.
- Update Workbench docs/code when HTTP routes, prompts, UI logic, or user-facing
  configuration changes.
- Keep VMC docs focused on Python package behavior and entry points.

## PR Checklist

- [ ] Tests cover the changed behavior.
- [ ] `pytest model_checker/tests/` or the relevant focused subset passes.
- [ ] Docs are updated when behavior, setup, or public contracts changed.
- [ ] Benchmarks were run or considered for algorithm changes.
- [ ] Entry points in `pyproject.toml` are updated for new built-in logic.
- [ ] Cross-project changes are documented in the owning repo.
