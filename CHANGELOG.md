# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- A test checks the operator spacing rule for every registered logic
  (`test_operator_spacing.py`); a logic missing from its tables fails it. It covers
  the one-operand operators and the binary ones (`U`, and `R`, `W` where a logic has
  them): `p U q` is accepted, `pUq` is one name, `pU q` and `p Uq` are rejected, and
  a lowercase operator (`f p`, `p u q`) is rejected.
- ICTL accepts the path quantifier over a parenthesized or bracketed Until or
  Release, `A(p U q)` and `A[p U q]`, the forms the ICTL papers write (EUMAS 2025,
  AREA 2023). `A p U q` still works. Before, `A(p U q)` and `A[p U q]` failed with
  a syntax error.
- OL, TOL, RBATL, RABATL, CapATL and Wallet_ATL accept a parenthesized Until (and
  Release or Weak Until where the logic has them) after the prefix, such as
  `<J2> (p U q)` and `<1><5> (p U q)`. Every logic with a prefix before Until now
  takes both forms and builds one tree for them (`test_until_after_prefix.py`).
  See `docs/logic_knowledge_base.md`, "Until after a prefix".

### Changed

- NatATL, NatATL_Recall and NatATLF reject a bound `k` below 1, such as `<{1}, 0>F p`,
  with "Invalid bound 0: must be at least 1". Before, `k = 0` parsed and the solver
  returned false for every formula.
- Breaking: every logic spells the connectives `&&`, `||`, `!`, `->` or the words
  `and`, `or`, `not`, `implies`. A single `&` or `|`, and `>` as implication, are
  rejected everywhere. Before, ATL*, TCTL and TOL took `&` and `|`, Wallet_ATL also
  took `>`, and the other logics gave a bare "Syntax error". The shared lexer now
  reports an invalid character. See `test_connective_spelling.py` and
  `docs/logic_knowledge_base.md`, "Boolean Logic (Shared Syntax)".
- Breaking: in every logic with a prefix (coalition, path quantifier, bound or
  freeze), a connective after a prefix whose scope no parenthesis closes is a
  syntax error that gives the position and both readings: `<1>F p && q`,
  `<1> p U q && r`, `AF p && q`, `!<1>X p && q`. No defining paper states how they
  group. Before, most logics read `(<1>F p) && q`, while TCTL and TOL read
  `A (p U (q && r))`. Write `(<1>F p) && q` or `<1>F (p && q)`. See
  `docs/logic_knowledge_base.md`, "Prefix before a connective".
- Breaking: CTL takes square brackets only around an Until, `A[p U q]`, as the
  defining paper writes it (Clarke, Emerson, Sistla 1986, p. 246). Before,
  `[p] && q` and `AF [p]` parsed as parentheses.
- Breaking: ATL*: `<<1>> p U q` is `<<1>> (p U q)`, the coalition over the Until.
  A chained `U` (`p U q U r`) and `U` next to `&`, `|` or `->` (`p U q & r`,
  `p & q U r`) are syntax errors that ask for parentheses, and so is any
  connective after a coalition (`<<1>> p & q`). Before, `<<1>> p U q` parsed as
  `(<<1>> p) U q`, which failed with "a bare Until is not a state formula", and
  the other forms followed the LTL precedence of Spot. See
  `docs/ATL_STAR/algorithm.md`.
- Breaking: a temporal operator is a word of its own in every logic, so a name
  written with no space after an operator is no longer split. See
  `docs/logic_knowledge_base.md`, "Operators and names".
  - LTL: `Xp`, `FGp`, `AXp`, `AGAFp` and similar, in upper or lower case, are
    names. Write `X p`, `F G p`, `AX p`, `AG AF p`. `ltl_to_ctl` no longer splits
    them. `pUq` is a name too, so `ltl_to_ctl` leaves it alone; before, it
    rewrote it to `A(p U q)`. Write `p U q`.
  - LTL: a name that is not among the model's declared propositions is an error
    that names it ("Proposition(s) 'Goal' not among the model's declared
    propositions [...]"). Before, only all-lowercase names were checked, so a
    capitalised, numbered or glued name such as `Goal`, `p1` or `pUq` was
    silently false.
  - NatSL: the goal needs a space after its operator (`F goal`). `Fgoal`, and a
    goal with no operator such as `Goal`, are rejected with an error. The
    normalised formula in the result now reads `...:(x,1)F goal`.
  - NatSL: the goal operators `F`, `G`, `X` are uppercase only, and `not` is
    lowercase only. `f goal` and `NOT F goal` are rejected; before, the goal
    ignored case.
  - NatATL, NatATL_Recall and NatATLF: `<{1},1>Fa` and `<{1},1>fa` are rejected.
    Write `<{1},1>F a`.

### Fixed

- LTL: `ltl_to_ctl` is built from the parsed formula instead of regex rewriting.
  Before, `p U !q` was left unrewritten, and `p U q U r` became the left-grouped
  `A(A(p U q) U r)` although the parser groups it to the right. Now it is
  `A(p U A(q U r))`. Nested and parenthesised operands such as
  `((a && b)) U c` are handled. A formula the parser rejects raises a
  `ValueError` that names it, instead of being passed on unchanged.
- NatATL, NatATL_Recall and NatATLF read a proposition that starts with `F`, `G`,
  `X` or `U` (`Fuel`, `Goal`, `Until`) as an operator followed by the rest of the
  name, so `<{1},1>F Fuel` failed with a CTL syntax error. This is the same
  change as the NatATL entry under "Changed".
- A comment line (`#` or `//`) inside `Clocks`, `Clock_constraints` or `Invariants`
  of a timedCGS model is skipped, as in every other section. Before, it was read as
  a row and the model failed with "Malformed clock constraint" or "Malformed
  invariant", and a comment after the clocks replaced them.
- The wheel now includes `model_checker/knowledge/knowledge_bundle.json.gz`.
  Earlier releases left it out, so an installed package had no documentation
  bundle. The bundle is rebuilt from the current docs and source.

## [1.7.0] - 2026-11-05

### Added

- `ATL_STAR.synthesize_strategy(formula, filename, state=None)`, a separate
  entry point returning a JSON-serializable witness strategy
  (`{"satisfied": bool, "strategy": {"start": ..., "moves": [...],
  "transitions": [...]} | None, ...}`), kept out of
  `model_checking` so that one stays focused on plain model checking. Only
  supports a formula whose outermost operator is a single coalition with
  no further coalition nested inside its path formula. Broader formula
  shapes are rejected with a clear "semantic" error, deferred to a later
  iteration. See `docs/ATL_STAR/algorithm.md`.
- `ObstructionModel`, the model type for COTL: a graph whose edges demons
  disable at a cost (sections `Number_of_demons`, `Demon_actions`, `Curses`;
  see `docs/file_formats.md`).
- COTL weak next `WX`, an empty legion `<><n>`, and budget 0.
- OATL accepts `R`, `W`, the parenthesised form `<A><n> (phi U psi)`, and
  budget 0.

### Changed

- **Breaking:** OATL now follows Catta et al., "Obstruction Alternating-time
  Temporal Logic", AAMAS 2024. `<A><n>` means the Demon erases joint actions of
  total cost at most `n` per step so that, whatever `A` does, some remaining
  path satisfies the formula. Earlier versions checked whether `A` had one
  move of cost `<= n` into the target. Recompute OATL results. A missing cost
  that decides the result is now an error instead of 0, and the ATL prefilter
  is dropped.
- **Breaking:** COTL now follows Catta et al., "Coalition Obstruction Temporal
  Logic", IJCAI 2025. `<G><n>` is a legion of demons with budget `n` per step.
  Earlier versions ran a cost-bounded coalition on a `costCGS`. Recompute COTL
  results and convert models to `ObstructionModel`; `costCGS` files are now
  rejected. `R`, `G` and `W` also hold on a path that stops because every edge
  out of its last state is disabled.
- OATL and COTL no longer share parser or pre-image code.
- `spottl` (Spot's Python bindings, Linux only) is now a regular
  dependency instead of living under the `atl_star` extra. `pip install
  vitamin-model-checker` alone is enough for ATL* to work, no
  `[atl_star]` extra needed.

### Fixed

- ATL_STAR's elimination algorithm could generate a fresh marker
  proposition (`__atl_star_elim_N`) that collided with a real proposition
  already declared in the model, silently corrupting the result for that
  edge case. The marker is now checked against the model's declared
  propositions before use.

### Removed

- `shared/oatl_index_preimage.py`.

## [1.6.5] - 2026-09-15

### Fixed

- NatSL formulas with spaces around `:` or between quantifiers (for example
  `E{1}x : (x, 1) F goal`) no longer fail with
  `Invalid quantifier near ' '; expected E{k}x or A{k}x`. The parser now strips
  the quantifier prefix and binding/goal suffix and accepts flexible whitespace
  inside quantifier and binding tokens.

## [1.6.4] - 2026-09-11

### Added

- ATL* model checking (`model_checker/algorithms/explicit/ATL_STAR/`), an
  automata-theoretic checker (reduction to 2-player parity games) rather
  than the coalition pre-image fixpoint every other logic here uses. It is
  needed because ATL* allows a coalition operator to appear anywhere
  inside a path formula, not only at the formula's own root. Runs over
  plain `CGS`, no new game-structure type. Requires
  [Spot](https://spot.lre.epita.fr/) (`pip install spottl` on Linux, or
  conda-forge elsewhere); the rest of VITAMIN works without it, see
  `docs/ATL_STAR/algorithm.md`.
- `model_checker/automata/`, a vendored, logic-agnostic omega-automata and
  parity-game-solving library (wraps Spot) backing ATL*'s reduction. It is
  available to any future logic that needs the same machinery.
- Restricted executable NatSL one-goal checker with ordered bounded strategy
  quantification and shared `space`/`time` semantics.
- Multi-character NatSL strategy variables.
- NatSL semantic regression tests and dedicated CGS fixtures.
- Runnable NatSL examples, including a logistics-robot case study.
- Reproducible NatSL scalability benchmark with curated recorded results.
- NatSL success payloads now include NatATL-style `res` / `initial_state`
  fields alongside `Satisfiability` for backend compatibility.

### Changed

- Mixed bounded NatSL prefixes are evaluated directly instead of being
  decomposed into independent NatATL checks.
- NatSL uses exact action pruning: strategies selecting unavailable actions are
  treated as inadmissible rather than repaired with an implicit idle action.
- NatSL documentation now describes the implemented `E* A*` one-goal fragment
  and its deliberate boundaries.
- Public NatSL algorithm entry is a single `NatSL` entry point
  (`core.model_checking` with `mode="space"|"time"`). The
  `NatSL_Sequential` / `NatSL_Alternated` packages and entry points were removed.

### Fixed

- NatSL runnable examples used a misspelled `Unkown_Transition_by` header that
  broke CGS loading; examples are synced with the correct fixtures.

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
