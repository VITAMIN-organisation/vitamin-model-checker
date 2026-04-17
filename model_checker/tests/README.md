# Tests overview

This document explains how the test suite is organised, how to reuse the common helpers, and how to run only the pieces you care about.

## Directory layout

All tests live under `model_checker/tests`:

- `unit/` - fast, focused tests for individual functions, parsers, and small algorithm pieces.
- `integration/` - end-to-end logic tests over real models (correctness and semantics).
- `e2e/` - full "user workflow" tests that go through the public API.
- `performance/` - performance and scalability tests that enforce time limits.
- `helpers/` - shared helpers used by the tests (model loading, builders, assertions).

## Fixtures and test data

All model and test data live under `tests/fixtures/`: valid models in `fixtures/{CGS,costCGS,capCGS}/{LOGIC}/`, invalid and edge-case files in `fixtures/tests/{invalid,edge_cases}/`. Tests either load from `test_data_dir` or build small models in memory via `tests/helpers/model_helpers.py`.

Common fixtures are defined in `tests/conftest.py`:

- `test_data_dir` - path to `tests/fixtures/`. Use with
  `load_test_model(test_data_dir, "CGS/ATL/...")`. Invalid and edge-case files
  live under `fixtures/tests/`.
- `temp_file` - helper that writes a string of model content to a temporary file
  and returns its path. Used by tests that construct models on the fly.
- `cgs_simple_parser` - a pre-loaded parser for `atl_2agents_4states_simple.txt`,
  so tests that just need "some small CGS" don't have to load it themselves.

Some logics have an extra conftest under their integration folder, for example
`integration/algorithms/cotl/conftest.py`, which provides `cotl_model_path` for
COTL tests.

## Shared helpers

Helpers live in `tests/helpers/` and are imported by both unit and integration tests.

- `model_helpers.py`
  - loading: `load_test_model`, `load_cgs_from_content`, `load_costcgs_from_content`
  - content builders: `build_cgs_model_content`, `generate_linear_chain`,
    `generate_cycle_model`, `generate_cost_cgs_linear_chain_content`, ...
  - result parsing: `extract_states_from_result` (turns the checker's `res` field
    into a Python `set`)
  - formula parsing: `assert_parse_structure` for quick sanity checks on
    formula parse trees

COTL integration tests also use
`integration/algorithms/cotl/cotl_test_helpers.py` for small helpers such as
`check_and_get_states`, `result_states`, and `load_cotl_parser`.

Performance tests share a small helper module in
`tests/performance/performance_helpers.py`:

- `check_parser_performance` - builds and parses a generated model and asserts
  that parsing finishes under a given time bound.
- `run_model_checking_with_timeout` - runs a model-checking call in a separate
  thread, enforces a timeout, and returns `(states, elapsed_time)`.

## Unit tests (`unit/`)

Unit tests are deliberately small and cheap. They exercise:

- formula parsing
- model file parsing and validation
- CGS / costCGS API helpers
- low-level algorithm pieces (fixpoints, transition caches, tree building, etc.)

### Formula parsers

`unit/parsers/formulas/` contains smoke tests that only care about syntax and
basic structure:

- `test_formula_parsers_smoke.py` - one parametrised test that checks the
  per-logic formula parsers (ATL, CTL, LTL, NatATL, OATL, OL, RBATL, NatSL,
  CapATL) accept valid inputs and reject invalid ones.

### Model parsers and CGS API

`unit/parsers/models/` covers the file-level parsers and core CGS API:

- `test_model_file_parsing.py` - missing sections, malformed matrices, labelling
  rules, duplicate sections, and cost/cap extension sections.
- `test_cgs_api.py` - convenience methods on the CGS object
  (`get_number_of_agents`, `get_actions`, `get_coalition_action`,
  `get_opponent_moves`, etc.).
- `test_cgs_validation.py` - structural validation of parsed models
  (`validate_model_structure`).

### Algorithm-level unit tests

`unit/algorithms/` contains tests that focus on algorithm internals, without
running the full model-checking loop.

- `test_witness_counterexample.py` - shared across logics; exercises
  `VerificationResult`, trace types, and `extract_shortest_trace`.

Logic-specific algorithm unit tests live under `unit/algorithms/<logic>/`:

- `unit/algorithms/atl/test_fixpoint_cache.py` - ATL fixpoint computation and
  transition cache building.
- `unit/algorithms/ltl/test_ltl_to_ctl.py` - LTL-to-CTL formula conversion.
- `unit/algorithms/natatl/test_matrix_parser.py` - NatATL idle-matrix validation
  (`validate_nat_idle_requirements`).
- `unit/algorithms/natatl/recall/` - NatATL-recall helpers:
  `test_tree_building.py`, `test_boolean_pruning.py`, `test_strategy_generation.py`.

### Utilities

- `unit/utils/test_bit_vector.py` - tests for the bit-vector state-set helper
  used by some algorithms.

## Integration tests (`integration/`)

Integration tests wire together real models, the public model-checking API, and
selected helpers. They live under:

- `integration/parsers/` - parser integration tests
- `integration/algorithms/<logic>/` - per-logic correctness and semantics
- `integration/interface/` - cross-logic API tests

### Parser integration

- `integration/parsers/test_valid_models_structure.py` - loads a representative
  set of fixture models and checks that transition and labelling matrices are
  dimensionally consistent, state indexes and names round-trip correctly, and
  atomic propositions can be looked up by name.

### Logic-specific integration tests

Each logic has a folder under `integration/algorithms/<logic>/`. Not every
logic has the same files, but the pattern is consistent:

- `test_correctness.py` - API and error handling (invalid formulas, invalid
  coalitions, missing atoms, etc.). Some also contain basic satisfiability
  checks.
- `test_semantics.py` - expected state sets for key formulas on small models.

On top of that, some logics have extra coverage:

**CTL** (`integration/algorithms/ctl/`)

- `test_correctness.py` - API and error handling.
- `test_semantics.py` - expected state sets on simple and custom models.
- `test_ctl_edge_cases.py` - cycles, deadlocks, and combinations on small
  models.
- `test_complex_formulas.py` - deeply nested temporal operators (for example
  `EF(AG(EX p))`).
- `test_corner_cases.py` - single-state model with a self-loop, checking
  `EF`, `EG`, `AF`, `AG`.
- `test_fixpoint.py` - fixpoint convergence for `EF`, `AF`, `EG`, `AG`.
- `test_preimage.py` - `pre_image_exist` and `pre_image_all`.
- `test_trace_generation.py` - witness / counterexample trace generation.

**ATL** (`integration/algorithms/atl/`)

- `test_correctness.py` - API and error handling.
- `test_semantics.py` - expected state sets on simple ATL models.
- `test_critical_paths.py` - coalition pre-image when an opponent can spoil the
  outcome.

**NatATL** (`integration/algorithms/natatl/`)

- `memoryless/` - `test_correctness.py`, `test_semantics.py`.
- `recall/` - `test_correctness.py`, `test_critical_scenarios.py`.

Other logics (OATL, OL, RBATL, RABATL, CapATL, etc.) follow the same
`test_correctness.py` / `test_semantics.py` pattern in their own folders.

### Interface tests

- `integration/interface/test_model_checker_api.py` - covers the
  cross-logic API surface: running different logics through the same entry
  point and checking that results and error paths are consistent.

## End-to-end tests (`e2e/`)

The `e2e/` directory contains a small number of tests that simulate how a user
would actually call the library:

- `test_full_workflows.py` - loads models, runs model checking for several
  logics, exercises error handling for invalid files, runs a "large model /
  complex formula" scenario, and checks strategy extraction.

## Performance tests (`performance/`)

Performance tests are pass/fail and enforce explicit time limits. They are
marked with `@pytest.mark.performance` and live under `performance/`:

- `test_atl_performance.py`, `test_ctl_performance.py`, `test_oatl_performance.py`,
  `test_natatl_performance.py`, `test_scalability.py`, etc.
- Most tests use `run_model_checking_with_timeout` and/or
  `check_parser_performance` from `tests/performance/performance_helpers.py`.

These tests are meant to catch regressions (for example, a change that makes
`EF p` suddenly 10x slower), not to provide fine-grained benchmark numbers.

## Benchmarks

Benchmarks are no longer part of the pytest test suite.
Use the benchmark tool in `model_checker/benchmarking/README.md`.

## Markers and how to run tests

Markers are registered in `tests/conftest.py` and can be combined in expressions
such as `-m "unit and atl"` or `-m "integration and not performance"`.
The main markers are:

- `unit` - unit tests
- `integration` - integration tests
- `semantic` - semantics-level tests
- `parser` - parser tests
- `validation` - model validation tests
- `model_checking` - model-checking core
- `edge_case` - edge and corner cases
- `robustness` - robustness and error handling
- `performance` - performance tests
- `e2e` - end-to-end tests
- `workflow` - workflow-oriented tests

Typical commands:

- all tests:
  `pytest model_checker/tests/`
- only unit tests:
  `pytest model_checker/tests/unit/`
- only integration tests:
  `pytest model_checker/tests/integration/`
- only e2e tests:
  `pytest model_checker/tests/e2e/`
- filter by marker, for example integration only:
  `pytest model_checker/tests/ -m integration`
