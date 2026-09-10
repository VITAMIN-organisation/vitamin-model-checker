# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Restricted executable NatSL one-goal checker with ordered bounded strategy
  quantification and shared `space`/`time` semantics.
- Multi-character NatSL strategy variables.
- NatSL semantic regression tests and dedicated CGS fixtures.
- Runnable NatSL examples, including a logistics-robot case study.
- Reproducible NatSL scalability benchmark with curated recorded results.

### Changed

- Mixed bounded NatSL prefixes are evaluated directly instead of being
  decomposed into independent NatATL checks.
- NatSL uses exact action pruning: strategies selecting unavailable actions are
  treated as inadmissible rather than repaired with an implicit idle action.
- NatSL documentation now describes the implemented `E* A*` one-goal fragment
  and its deliberate boundaries.

## [1.6.3] - 2026-08-26

### Fixed

- `detect_model_type_from_content` recognizes ICTL BirelationalMatrix files
  whose Transition cells use only `0` / `R` / `P` / `P,R` (with a `P` or
  `P,R` marker), instead of classifying them as plain CGS.

## [1.6.2] - 2026-08-25

### Added

- Dedicated COTL parser package; CapATL binary Release (greatest fixpoint).
- Per-logic algorithm docs, architecture/structure docs under docs/.
- Stronger unit/integration coverage (WalletCGS, timedCGS, bounded ATL, parsers).

### Changed
- Parser layout standardized across logics; PLY parsetab files renamed per logic.
- Shared boolean AST allow-lists; Release/Weak Until grammar moved to COTL
  (dropped from OATL/RBATL surface).
- Explicit checkers: unified error/loading paths, thread-safe PLY parsing,
  reused loaded models, fail-closed n_agent defaults.

### Fixed
- Semantics: CTL ER duality; ATL compact joint actions; CapATL Pre/F;
  LTL/TCTL/TOL/ICTL/RBATL theory alignment; Wallet_ATL next/feasibility/until;
  OATL multi-resource costs; NatSL Alternated challenges; NatATL coalition
  validation.
- Models: total CGS transitions (no vacuous AX on sinks); CostCGS keys; timedCGS
  invariants/zones/constraints; model_factory header detection; BCGS factory via
  CGS.

## [1.6.0] - 2026-06-24

### Added

- Logics and entry points for ICTL, IATL, TOL, and TCTL (parsers, metadata, and
  model-checking modules).
- CI checks for wheel/sdist builds, `twine check`, and `mkdocs build --strict`.
- TCTL regression fixtures and tests where AF differs from AG and AU differs
  from EU (`tctl_af_regression.txt`, `tctl_au_regression.txt`).

### Changed

- **Packaging:** Runtime dependencies are declared only in `pyproject.toml`.
  Removed twelve unused packages that were not imported by `model_checker`
  (`automata-lib`, `networkx`, `antlr4-python3-runtime`, `requests`, and
  others). Only `ply`, `numpy`, and `pydantic` are required at install time.
- **Python:** Supported versions are Python 3.11 and 3.12 (`requires-python =
  >=3.11`). Black and Ruff `target-version` settings were aligned with this.
- **Metadata:** Added license, Trove classifiers, keywords, and project URLs for
  the PyPI project page.
- **Version reporting:** `model_checker.__version__` reads the installed
  distribution version from package metadata.
- **Error API:** Consolidated error helpers into `create_error_response(type,
  message)`. The per-type wrappers (`create_syntax_error`, `create_semantic_error`,
  `create_model_error`, `create_system_error`, `create_validation_error`) were
  removed from the public API; callers use `create_error_response` directly.
  The `res` / `initial_state` string fields are unchanged for backward
  compatibility with existing consumers.
- **Typing:** Modernised annotations across the codebase to PEP 585/604 style
  (`dict` instead of `Dict`, `X | Y` instead of `Union`, and so on) so `make
  lint` passes under Ruff with `target-version = "py311"`.
- **Documentation:** Clarified NatATL Recall PrefilterATL (ATL parse validation
  only, no satisfiability gate), `Node` state renaming after pruning, and TCTL
  fixpoint definitions in `docs/TCTL/algorithm.md`.

### Fixed

- **TCTL:** `AF` used the same least-fixpoint complement as `AG` instead of
  `All \ EG(not phi)`; corrected to a greatest-fixpoint formulation.
- **TCTL:** `A[phi U psi]` used an existential timed predecessor where a
  universal backward step (`AX`) is required; aligned with the CTL dual
  formulation.
- **TOL:** `ClockExpr` now intersects clock-guard regions with the subject
  formula (matching TCTL region-level behaviour at the location-name layer).
- **TOL:** `FreezeExpr` handler signature aligned with `ClockExpr`; freeze at
  the location-name abstraction remains a no-op when clock reset does not change
  the location.

### Removed

- `setuptools` as a runtime dependency (it remains a build-time requirement
  only).
- Dead NatATLF modules `strategies.py` and `pruning.py` (Recall delegates to
  NatATL Memoryless; these copies were unused and outdated).
