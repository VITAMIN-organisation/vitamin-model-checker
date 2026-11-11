# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- ICTL accepts `A(p U q)` and `A[p U q]`, and the same around Release (`A(p R q)`),
  as the ICTL papers write them (EUMAS 2025, AREA 2023). `A p U q` still works.
  Before, `A(p U q)` and `A[p U q]` were syntax errors.
- OL, TOL, RBATL, RABATL, CapATL and Wallet_ATL accept a parenthesized Until after
  the prefix (the coalition, bound or similar part before the temporal operator),
  such as `<J2> (p U q)` and `<1><5> (p U q)`, and the same for Release (`R`) or
  Weak Until (`W`) where the logic has them. Every logic with a prefix now takes
  `prefix p U q` and `prefix (p U q)` and builds one tree for both. See "Until after
  a prefix" in `docs/logic_knowledge_base.md`.
- Tests for operator spacing, the Until forms and connective spelling in every
  logic (`test_operator_spacing.py`, `test_until_after_prefix.py`,
  `test_connective_spelling.py`), and one that pins NatSL's "Unsupported goal"
  error for a connective in a goal such as `E{1}x:(x,1) F p && q`, as before
  (`test_natsl_spacing.py`).

### Changed

- Breaking: a WalletCGS file needs a `Wallets` row for every state. Before, a state
  with no row loaded and was read as holding 0 for every agent; loading now fails
  with `Wallets has no row for state(s) s1; ...`, since the Wallet ATL paper
  (AAMAS 2026, Def. 3.1) gives every agent a balance in every state. To keep the
  old result, add a row of zeros for that state.
- Breaking: CTL with `generate_trace=True` always returns the full result (`res`,
  `initial_state`, `satisfied`, `states`, `trace`, `strategy`, `metadata`), and
  `trace` is `None` when the outermost operator is a false E-operator (`EX`, `EF`,
  `EG`, `EU`), a true A-operator (`AX`, `AF`, `AG`, `AU`), a boolean connective or
  an atom. Before, every formula got a trace, so code that reads
  `result["trace"]["states"]` must now handle `None`. See "Traces" in
  `docs/CTL/algorithm.md`.
- Breaking: every logic spells the connectives `&&`, `||`, `!`, `->` or the words
  `and`, `or`, `not`, `implies`. A single `&` or `|`, and `>` as implication, are
  rejected with an "Invalid character" error. Before, ATL*, TCTL and TOL took `&`
  and `|`, Wallet_ATL also took `>`, and the other logics gave a bare "Syntax
  error". See "Boolean Logic (Shared Syntax)" in `docs/logic_knowledge_base.md`.
- Breaking: in every logic with a prefix (coalition, path quantifier, bound or
  freeze), a connective after a prefix that no parenthesis closes is a syntax error
  that gives the position and both readings: `<1>F p && q`, `<1> p U q && r`,
  `AF p && q`, `!<1>X p && q`. Write `(<1>F p) && q` or `<1>F (p && q)`. No defining
  paper states how they group. Before, most logics read `(<1>F p) && q`, while TCTL
  and TOL read `A (p U (q && r))`. See "Prefix before a connective" in
  `docs/logic_knowledge_base.md`.
- Breaking: a temporal operator is a word of its own in every logic, so `Xp` is one
  name and no longer `X p`. The one-letter operators are uppercase only (`f p` and
  `p u q` are rejected; word forms such as `until` and `eventually` still work), and
  a binary operator needs a space on both sides: `pUq` is one name, and `pU q` and
  `p Uq` are errors. See "Operators and names" in `docs/logic_knowledge_base.md`.
  - LTL: `Xp`, `FGp`, `AXp`, `AGAFp` and similar, in either case, are names, and
    `ltl_to_ctl` no longer splits them. Write `X p`, `F G p`, `AX p`, `AG AF p`.
    `pUq` is a name too, so `ltl_to_ctl` leaves it alone; before, it rewrote it to
    `A(p U q)`. Write `p U q`.
  - LTL: a name that is not among the model's declared propositions is an error
    that names it ("Proposition(s) 'Goal' not among the model's declared
    propositions [...]"). Before, only all-lowercase names were checked, so `Goal`,
    `p1` and `pUq` were silently false.
  - NatSL: the goal needs a space after its operator (`F goal`), so `Fgoal` and a
    goal with no operator such as `Goal` are rejected. The operators `F`, `G`, `X`
    are uppercase and `not` is lowercase: `f goal` and `NOT F goal` are rejected,
    where the goal ignored case before. The normalised formula in the result now
    reads `...:(x,1)F goal`.
  - NatATL, NatATL_Recall and NatATLF: `<{1},1>Fa` and `<{1},1>fa` are rejected.
    Write `<{1},1>F a`.
- Breaking: CTL takes square brackets only around an Until, `A[p U q]`, as the
  defining paper writes it (Clarke, Emerson, Sistla 1986, p. 246). Before, `[p] && q`
  and `AF [p]` parsed with the brackets as parentheses.
- Breaking: ATL* reads `<<1>> p U q` as `<<1>> (p U q)`, the coalition over the
  Until, as the ATL paper does (JACM 2002, p. 689). A chained `U` (`p U q U r`), a
  `U` next to `&&`, `||` or `->` (`<<1>> (p U q && r)`, `<<1>> (p && q U r)`) and
  any connective after a coalition (`<<1>> p && q`) are syntax errors that ask for
  parentheses. Before, `<<1>> p U q` parsed as `(<<1>> p) U q` and failed with "a
  bare Until is not a state formula", and the other forms followed the LTL
  precedence of the Spot library. See `docs/ATL_STAR/algorithm.md`.
- Breaking: NatATL, NatATL_Recall and NatATLF reject a bound `k` below 1, such as
  `<{1}, 0>F p`, with "Invalid bound 0: must be at least 1". Before, `k = 0` parsed
  and the solver returned false for every formula.
- TCTL rejects the next operator (`X p`, `AX p`, `EX p`, `A next p`) with a message
  such as "TCTL has no next operator ('AX' at position 1): time is dense, so there
  is no unique next state" (Alur, Courcoubetis, Dill, Information and Computation
  1993, p. 10). Before, the error was "Syntax error near token 'X'". Names such as
  `Xray` still parse.
- Tests: the `e2e/` folder is removed; its three tests repeated integration tests.
  Markers that no test used are removed from `pyproject.toml` (`slow`, `e2e` and
  others), so `make test` no longer filters with `-m "not slow"`. The test
  `README.md` states what a test must assert to be kept.
- Tests: the formula parser tests check each shared rule once, over every logic:
  reserved words and proposition names, coalition checks, connective precedence,
  word operators such as `eventually` and `until`, and an operator with no operand
  (`test_proposition_names.py`, `test_coalition_validation.py`,
  `test_precedence.py`). Eleven files that repeated these checks for a few logics
  are merged into these or removed.
- Tests: the model file tests assert exact results. Every broken fixture in
  `tests/fixtures/tests/` is checked for its message, every valid fixture must load
  (`test_fixture_models_load.py`), and `BitVectorStateSet` is compared with a Python
  `set` on random inputs. Seven files that repeated each other or checked only types
  are merged or removed, and the bit vector and NatATL idle tests move next to the
  code they test.
- Tests: the algorithm unit tests compare with results worked out by hand. They
  cover an opponent who can escape, a joint action with two outcomes, the bit
  vector path at 300 states, cost bounds that remove a move in RBATL and RABATL, the
  trace length limit, and every ICTL and IATL frame check. Tests that recomputed the
  code's own formula, checked only types, or tested CTL release handlers that no
  formula reaches are removed.
- Tests: the automata tests check that the sink added by `complete()` loses under
  Büchi, co-Büchi and all four parity orientations, and the solver cross-check
  compares both solvers with hand-computed winning regions. The test-only
  attractor oracle moves from `model_checker/automata/games/_attractor_oracle.py` to
  `model_checker/tests/helpers/attractor_oracle.py`, so it no longer ships in the
  package. Tests of enum members, dataclass defaults and import wiring are removed.
- Tests: CTL, ATL and ATL* each have one semantics file whose expected state sets
  are worked out from the model, with a reason per row; CTL's eight test files and
  ATL's three become two and one. A new `test_error_contract.py` runs every
  registered logic on a valid formula, a formula cut short, an undeclared
  proposition and an agent the model lacks. CTL trace tests check the trace type
  and that the path follows real edges.

### Fixed

- Wallet_ATL ignored some guards silently: a guard on an agent outside the
  coalition (`<<1:wallet(2, >= 100)>>X goal` ignored it), and all but the last
  guard on the same agent (`wallet(1, >= 100) && wallet(1, >= 5)` checked only
  `>= 5`). A guard outside the coalition is now a syntax error that names the
  agent, and every guard of a formula must hold, so
  `wallet(1, >= 3) && wallet(1, <= 5)` is a range. An exception raised while
  checking a guard now reaches the user instead of being read as "guard fails".
- Wallet_ATL X, F and U also required the guard at the state the move leads to,
  so `<<1:wallet(1, >= 10)>>X goal` and `F goal` were false at a state holding 10
  whose successor (where goal holds) holds 5. They now follow the Wallet ATL
  paper's Algorithm 1 (AAMAS 2026, lines 9 and 18-25), so a state where `goal`
  holds counts for F and U even if the guard fails there. See
  [Wallet_ATL operators](docs/Wallet_ATL/algorithm.md#operators).
- Wallet_ATL ignored the wallets when it built the coalition's moves, so an agent
  with 5 could still win through a `D20` move: `<<1>>X goal` was true where the
  Wallet ATL paper (AAMAS 2026, Def. 3.1 and 4.1) makes it false. The pre-image now
  uses only moves every agent can pay for, and a state with no affordable move is
  an error that names the state.
- WalletCGS: an income action no longer needs funds in the last agent's wallet;
  the paper allows income and neutral actions always.
- ICTL, IATL and ATLF: `true` and `false` were rejected with "does not evaluate the
  constant". They now mean all states and no state (in ATLF the value 1 and 0 everywhere).
- `true` and `false` are reserved words, so a model that declares a proposition with
  either name (in any letter case) is rejected. Before, `<1>F true` silently used the
  constant and ignored the model's own proposition.
- RBATL, RABATL and Wallet_ATL: when the initial state was False, the result was the
  state set of plain ATL, which is too large (RBATL `<1><1>G r` on the 6-state fixture
  listed s1, s3 and s4 instead of none), and an invalid bound such as `<1><0>G r` was
  accepted. The ATL prefilter is removed, so the full check always runs.
- CapATL: a proposition name with a letter and a digit (`p1`) was read as a capacity
  reference and rejected as unknown. Every leaf is now a proposition name, as in the other
  logics. Capacities are written `a is c` inside `K`, as the docs say.
- timedCGS: a strict invariant such as `x<3` was applied as `x<=3` because the parser
  dropped the operator. Time now stops before the bound.
- OL follows its paper (ECAI 2023, Definitions 3-4). In `<Jk> phi` a Demon, at
  each step, disables edges of the current state whose costs sum to at most `k`,
  never all of them, and every remaining path must satisfy `phi`. Before, `k`
  limited the total cost of the cheapest path, a reading the paper does not
  define, and the `W` operator swapped the two arguments of the `R` operator. For
  example, on `ol_testvitamin_2agents_8states.txt` the formula `<J26> F goal` was
  False although the only path from state 0 reaches goal. OL runs the OATL
  operators with the coalition of all agents, as AAMAS 2024 (section 6) relates
  the two logics. `<J0>` is valid, since the paper takes the bound in N0, and
  `<J01>` is refused with a message that names it. `Transition_With_Costs` models
  give each cell as one edge with its cost (see `docs/OL/algorithm.md`,
  `model_checker/tests/integration/algorithms/ol/test_correctness.py`).
- OL results in the VITAMIN Workbench change with the fix above; the Workbench is
  updated in its own repository.
- OATL: a missing action cost that decides a result is an error of type `model`,
  not `system`. A coalition other than all agents on a `Transition_With_Costs`
  model is a `model` error, because such a model has no joint actions.
- TCTL and TOL: a name the model does not declare is a semantic error that names
  it. Before, it was read as a proposition false everywhere, so `AG !zz` held. LTL's
  Nash and sure-win functions (`model_checking_sure_win`, `model_checking_exists_nash`
  and the others that call `initialize`) check names too; before, `F zz` gave a
  verdict there. NatATLF reports an undeclared name as `semantic`, not `system`, and
  NatATL, NatATL_Recall and NatATLF name it in the message. LTL reports it as
  `semantic` instead of `validation`, with the same message. See "Operators and
  names" in `docs/logic_knowledge_base.md` (`test_error_contract.py`).
- Every logic names an undeclared proposition in its error ("Proposition(s) 'zz'
  not among the model's declared propositions [...]"). Before, ATL, ATLF, CTL,
  CapATL, COTL, IATL, ICTL, OATL, OL, RABATL, RBATL and Wallet_ATL said only that
  the atom does not exist, and IATL and ICTL called it a syntax error. A constant the
  logic does not evaluate, such as `true` in ICTL, IATL and ATLF, is named as such.
- LTL: `res` reads `Result: True` or `Result: False`, as in NatATL. Before, it was
  the literal text `Result: {satisfied}` or `Result: {}`.
- LTL, NatATL, NatATL_Recall and NatATLF refuse a model proposition named `A`, `E`,
  `AF` or another name the CTL parser reads as an operator, with a semantic error
  that names it. Before, such a name gave wrong verdicts: these logics check
  through CTL text, where `A` is a path quantifier, and the failed CTL checks of
  strategy conditions were read as "holds nowhere" and the failed goal check as
  False. A failed inner CTL check now raises instead.
- ATL*: a proposition whose name starts with a Spot operator letter, such as
  `Granted`, `Fuel` or `Xray`, gave a wrong verdict or a "RuntimeError:
  unimplemented", because Spot read `Granted` as `G(ranted)`. Names are now quoted
  in the text passed to Spot (`test_verifier.py`).
- CapATL: the knowledge operator K^a_cap of AAMAS 2024 (p. 125-126) parses, typed
  `K1(1 is c)` or `kcap1(1 is c)`, alone or inside a formula such as
  `<{1}> F (g && K2(3 is c || 3 is cop))`. Inside the parentheses only
  `agent is capacity`, `!`, `&&`, `||`, `->`, `true` and `false` are allowed. A `K1`
  without parentheses, a `K` inside another, a proposition inside it and an agent
  out of range are errors that name the part. Before, no K formula parsed: `K1` was
  read as a proposition name, and `K 1 (1 is c)` returned no result and no error.
  The solver has no K semantics yet, so model checking a formula with K returns a
  `validation` error, "The knowledge operator K1(...) is parsed but not evaluated
  by the CapATL solver yet". See `docs/CapATL/algorithm.md`.
- LTL: `ltl_to_ctl` is built from the parsed formula instead of regex rewriting.
  Before, `p U !q` was left unrewritten, and `p U q U r` became the left-grouped
  `A(A(p U q) U r)` although the parser groups it to the right; now it is
  `A(p U A(q U r))`. Nested and parenthesised operands such as `((a && b)) U c`
  work. A formula the parser rejects raises a `ValueError` that names it, instead
  of being passed on unchanged.
- NatATL, NatATL_Recall and NatATLF: a name that starts with `F`, `G`, `X` or `U`
  (`Fuel`, `Goal`, `Until`) is a name, so `<{1},1>F Fuel` parses. Before, it was read
  as an operator followed by the rest of the name and failed with a CTL syntax error.
- A comment line (`#` or `//`) inside `Clocks`, `Clock_constraints` or `Invariants`
  of a `timedCGS` model file is skipped, as in every other section. Before, it was
  read as a row and the model failed with "Malformed clock constraint" or
  "Malformed invariant", and a comment after the clocks replaced them.
- The PyPI package includes `model_checker/knowledge/knowledge_bundle.json.gz`,
  rebuilt from the current docs and source. Earlier releases left it out, so an
  installed package had no documentation bundle.
- CTL traces (`generate_trace=True`) were always the initial state alone, for
  every formula. A true `EX`, `EF` or `EU` now gives a witness path to a state
  that satisfies the operand, and a true `EG` a witness lasso. A false `AX` or
  `AG` gives a counterexample path to a state that violates the operand, a false
  `AF` a counterexample lasso (a path that ends in a loop), and a false `AU` a
  path or a lasso. A lasso lists each state once in `trace["states"]`, and the new
  key `trace["cycle_start_index"]` is the index its last state steps back to; it
  is `None` for a path.
- CTL with `generate_trace=True` printed `res` as an unordered set
  (`Result: {'s3', 's0'}`). It is now the sorted tuple that the result without a
  trace prints (`Result: ('s0', 's3')`).

### Removed

- Breaking: WalletCGS `get_valid_actions`, `get_next_states` and
  `simulate_transition`. Wallet_ATL never called them. With more than one agent
  they treated the last agent as the contract and skipped its wallet check,
  which the Wallet ATL paper (AAMAS 2026, Def. 4.1) does not do.
  `simulate_transition` also moved each amount to or from that agent; the
  paper's section 3.2 does this and its Def. 4.4 does not. For wallet
  feasibility use `check_action_feasibility` and `is_profile_feasible`. Nothing
  replaces the next-state and balance-update helpers: balances are not updated
  along transitions (see `docs/Wallet_ATL/algorithm.md`).
- Breaking: the helpers that only the old CTL traces used. From
  `algorithms.explicit.shared`: `reconstruct_trace_from_predecessors`,
  `build_predecessor_map_bfs`, `build_predecessor_map_forward`,
  `extract_shortest_trace` and `least_fixpoint_with_trace`. From
  `algorithms.explicit.CTL`: the module `operators_with_trace`,
  `preimage.pre_image_exist_with_trace`, `solver.solve_tree_with_trace` and
  `solver.extract_trace_for_result`. Also the `max_length` parameter of
  `reconstruct_trace_bfs`; the limit is `MAX_TRACE_LENGTH`. `solver.solve_tree`
  labels the tree, and
  `traces.build_trace` builds the trace with `reconstruct_trace_bfs` and
  `find_lasso` from `shared.trace_utils`.

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
