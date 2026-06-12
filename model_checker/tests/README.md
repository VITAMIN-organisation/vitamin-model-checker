# Model checker tests

This suite checks that the VITAMIN model checker parses inputs correctly, runs
algorithms as intended, and stays usable through the public API. The layout
follows a simple testing pyramid: small fast checks at the bottom, full
workflows at the top.

## What we are trying to guarantee

1. **Inputs are handled safely** - model files and formulas are parsed and
   validated; malformed or inconsistent inputs fail in a controlled way.
2. **Logics mean what they should** - on small, known models, satisfying state
   sets match expected semantics (not just "the code runs").
3. **The library behaves like a product** - the same entry points callers use
   in applications work across logics, including errors and edge cases.
4. **Regressions are caught early** - performance tests flag large slowdowns;
   unit tests pin down fragile internals before they break integration tests.

New logics and features should extend this guarantees, not bypass them.

## Layers (main idea)

Tests are grouped by **scope**, not by implementation detail. Deeper folders
mirror logics and components; the names on disk are the map.

```text
unit/           Isolated pieces: parsers, validators, algorithm helpers
integration/    Real models + model checking, wired as in production
e2e/            End-to-end paths a user or host application would take
performance/    Time-bounded checks for scalability regressions
fixtures/       Static model files and invalid/edge-case inputs
helpers/        Test-only utilities (loading fixtures, asserting on results)
```

**Unit** tests answer: "Does this function or class do the right thing in
isolation?" They should be fast and narrow. Prefer them for parser grammar,
matrix validation, fixpoint steps, conversion utilities, and shared data
structures.

**Integration** tests answer: "Given a real model and formula, does this logic
produce the right answer or the right error?" They are the main correctness
backbone per logic. Typical themes:

- **Semantics** - expected state sets on small models with known answers.
- **Correctness / API** - invalid formulas, bad coalitions, missing atoms,
  and other error paths through the public checker.
- **Logic-specific depth** - extra scenarios where a logic needs more than
  smoke coverage (fixpoints, pre-images, traces, recall strategies, etc.).

**E2E** tests answer: "Can someone load a model, run checking, and use the
result without touching internals?" Keep this layer thin; it guards the
overall workflow.

**Performance** tests answer: "Did we accidentally make common cases much
slower?" They use timeouts and coarse bounds, not micro-benchmarks. For
detailed pyperf benchmarking, see the separate
`vitamin-benchmark-model-checker` project.

## How tests get their models

Two complementary approaches:

- **Fixtures** - checked-in `.txt` models under `fixtures/`. Use these when
  the shape of the file matters (real game structures, cost/cap extensions,
  invalid files for error handling).
- **Synthetic models** - built in memory via `model_checker.synthetic_models`
  (and test helpers that load or assert on them). Use these when size or
  repetition matters (chains, cycles, scalability sweeps).

Pick the smallest model that still exercises the behavior under test.

## Markers and running tests

Markers in `conftest.py` describe **intent** (unit, integration, semantic,
parser, performance, e2e, etc.). Combine them when filtering, for example
only integration tests or everything except performance.

From the repository root:

```bash
pytest model_checker/tests/
pytest model_checker/tests/unit/
pytest model_checker/tests/integration/
pytest model_checker/tests/ -m performance
pytest model_checker/tests/ -m "integration and not performance"
```

Run the narrowest set that covers your change before opening a PR.

## Adding or changing tests

- Match the **layer** to the question you are asking (unit vs integration).
- Put logic-specific tests under that logic's folder; reuse shared helpers
  instead of copying model-loading or result-parsing code.
- Prefer one clear assertion per scenario; name tests after the behavior, not
  the function under test.
- If you add a new logic, aim for at least parser smoke coverage, integration
  correctness on a small fixture, and semantics on a model with known answers.

## VMI and integrated logics

When a logic bundle is integrated into this repository, run the relevant tests
here after VMI's post-integration checks pass. VMI verifies install and import;
this suite verifies that the core package still behaves correctly over time.
