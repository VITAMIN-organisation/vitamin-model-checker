# Model checker tests

This folder holds the tests of the model checker: unit tests of parsers and algorithm helpers, integration tests that run each logic on model files, and time-bound performance checks. The commands and the rules for a test that earns its place are below. See also [Run tests](../../README.md#run-tests) in the README.

## Layout

```text
unit/           One parser, validator or algorithm helper at a time
integration/    One logic on a model file, through its model_checking entry point
performance/    Large generated models with a time limit and an exact answer
fixtures/       Model files, by structure (CGS, costCGS, capCGS, WalletCGS,
                timedCGS, ObstructionModel) and logic; tests/invalid/ holds broken files
helpers/        Fixture loading, synthetic model builders, result parsing
```

Synthetic models come from `helpers/synthetic_models.py`; use them when the size or shape of the model matters more than its file format.

## Running

From the repository root:

```bash
uv run pytest model_checker/tests/unit model_checker/tests/integration -q
uv run pytest model_checker/tests/performance -q
uv run make test
```

CI runs unit and integration only. `make test` runs all three folders.

## What a test must do

A test stays only if a plausible bug in the source would make it fail:

- It asserts the exact result: the full set of satisfying states, the parse tree, or the error type and message. A key being present, a type, `len > 0` or `is not None` is not enough.
- Each expected state set comes with a one-line reason derived from the model (`# s2 loops on itself and q is false there`), not copied from the checker's output.
- It does not re-implement the code under test and compare the two.
- A behaviour is tested once. A rule shared by all logics, such as connective spelling, lives in one parametrized test over the logics.
- The docstring is one line: the behaviour checked and why it matters.

A wrong behaviour that is not fixed yet is not pinned by a test; it is reported as a bug.

## Markers

Markers are registered in `pyproject.toml` and checked with `--strict-markers`. The ones used for selection are `performance` (set for the whole folder) and `atl_star`.
