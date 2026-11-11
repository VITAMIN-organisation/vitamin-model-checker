# Algorithm Design

Shared implementation techniques used by the explicit checkers: data
structures, caches, cleanup, and search strategies.

## Technique Index

| Technique | Used by | Code |
|---|---|---|
| Transition move cache | `ATL`, `ATLF`, `IATL`, `Wallet_ATL`, `RBATL`, `RABATL`, `OATL`, `COTL` | `ATL/preimage.py`, `ATLF/preimage.py`, `IATL/preimage.py`, `shared/bounded_atl_preimage.py`, `OATL/preimage.py`, `COTL/preimage.py` |
| Bit-vector target sets | `ATL`, `RBATL`, `RABATL` | `shared/bit_vector.py` |
| Early-stop in pre-image | `ATL`, `Wallet_ATL` | `ATL/preimage.py` `early_stop` |
| AST solve memo cache | `RBATL`, `RABATL` (bounded ATL solver) | `shared/bounded_atl_solver.py`, `shared/solver_core.py` |
| CapATL lru + state index cache | `CapATL` | `CapATL/utils.py`, `CapATL/CapATL.py` |
| P-upset precompute | `ICTL`, `IATL` | `ICTL/util/graph.py` `get_preorder` |
| Zone graph | `TCTL`, `TOL` | `timed_cgs/zone_graph.py` |
| Obstruction filter (`triangle`) | `TOL` | `TOL/preimage.py` |
| Strategy pruning + condition cache | `LTL`, `NatATL`, `NatSL` | `LTL/pruning.py`, `NatATL/*/pruning*.py`, `condition_cache.py` |
| Performance regression tests | `ATL`, `CTL`, `OATL`, ... | `tests/performance/` |

## Transition Move Cache

**What:** One pass over the transition matrix builds, for each state, the list
of outgoing joint action profiles (and optionally groups them by coalition
move).

**Why:** Coalition pre-image `pre()` runs on every fixpoint step for `F`, `G`,
`U` (up to |S| iterations). Without a cache each step re-parses matrix cells
via `build_action_list`.

**How:** `build_transition_cache(cgs)` (or with a fixed coalition) before
`solve_tree`. Handlers pass the cache into `pre()`.

**Advantage:** Fixpoint iterations read stored move lists instead of
re-parsing the graph. Same asymptotic class per step, less constant work on
repeated scans.

**Variants:**

- `ATL` / `Wallet_ATL`: cache once for the whole solve (joint profiles; group by
  coalition on demand).
- `IATL`: lazy per-coalition cache on the checker (`transition_cache_for`).
- `ATLF` / `RBATL` / `RABATL`: build a coalition-grouped cache per operator
  call via ATLF or `shared/bounded_atl_preimage.py`.
- `OATL`: `DemonicPreimage` expands the matrix once per check, with each joint
  action's cost, and groups it by coalition move once per coalition.
- `COTL`: `LegionSteps` builds, once per legion, each state's legion actions
  with their cost and the successor sets the other demons can leave. Actions
  that no listed curse extends all leave every edge, so only the cheapest one
  is kept (best-first search, at most one candidate more than the listed
  curses). See [COTL/algorithm.md](COTL/algorithm.md#algorithm).

## Bit-Vector Target Sets

**What:** When `|S| >= 300` (`BIT_VECTOR_THRESHOLD`), the target set inside
`pre()` is a numpy bit array (`BitVectorStateSet`) instead of a Python set.

**Why:** Pre-image scans many destination indices and asks "is j in T?". On
large state spaces, set hashing is slower than indexed bit tests.

**How:** `shared/bit_vector.py`; branch in ATL and shared cost/resource
pre-image helpers.

**Advantage:** Cheaper membership on large models. Below 300 states, Python
sets stay because numpy setup cost is not worth it.

## Early-Stop In Pre-Image

**What:** Optional `early_stop` index set: if state `q` is already known to
satisfy the current fixpoint accumulator, skip coalition move enumeration for
`q`.

**Why:** Least-fixpoint growth for `F` / `U` already owns many states; they
need not be reclassified each iteration.

**How:** `pre(..., early_stop=p_indices)` from ATL / Wallet_ATL eventually and
until handlers.

**Advantage:** Fewer coalition grouping checks on states already in the
winning set.

## AST Solve Memo Cache

**What:** Dict from a node key to the already-computed state-set string while
walking the formula tree.

**Why:** Shared subformulas (or identical node shapes) can appear more than
once; recomputing the same denotation wastes work.

**How:** `shared/bounded_atl_solver.py` / `shared/solver_core.py` optional
`cache` argument.

**Advantage:** Subtree results reused within one solve.

## CapATL Caches And Cleanup

**What:**

- `build_state_cache`: state name -> index map on the CGS.
- `@lru_cache` helpers for capacity / successor / knowledge-related functions
  (`succ`, `Omega_Y`, ...).

**Why:** CapATL pre-image and knowledge helpers query state indices and
capacity combinations repeatedly.

**How:** At the start of each CapATL check, call `.cache_clear()` on the lru
functions, then `build_state_cache(cgs)`.

**Advantage:** Fast repeated lookups within one check; clear prevents results
from a previous model or formula leaking into the next check.

## P-Upset Precompute (Intuitionistic)

**What:** Transitive closure of the knowledge preorder `P`, stored as
`upward_closure[s] = s^up`.

**Why:** Intuitionistic `->` and `!` need `X^up = { s | s^up subseteq X }` on
every connective evaluation.

**How:** Built once in `ICTLModelChecker` / `IATLModelChecker` via
`get_preorder`.

**Advantage:** Constant-time upset lookup per state instead of recomputing
reachability along `P` for each connective.

## Zone Graph (Timed)

**What:** Symbolic regional transition system: nodes are `(location, zone)`
pairs with delay and discrete edges.

**Why:** Continuous clock valuations cannot be enumerated explicitly; zones
are a finite abstraction for TCTL / TOL.

**How:** `ZoneGraph(tcgs, ...)` after collecting formula clocks; operators
label regions (TCTL) or project to locations (TOL).

**Advantage:** Finite symbolic state space for timed model checking.

## Obstruction Filter (`triangle` / `triangle_down`)

**What:** TOL demonic step: among predecessors of `Z`, keep states where the
sum of deactivation costs of edges leaving `Z` is at most bound `k`.

**Why:** Implements per-position demonic budget without exploring full game
trees at every step.

**How:** `TOL/preimage.py`; used inside TOL fixpoints for `F` / `G` / `U` /
`R` / `W` / `X`.

**Advantage:** Direct set-based encoding of Definition 15 obstruction
predecessors.

## Strategy Pruning And Condition Cache

**What:** Enumerate natural strategies, prune the CGS (or execution tree) under
the strategy, then check a CTL-shaped goal. Condition results keyed by
`(condition, model)` are cached on the model object when the same propositional
condition is evaluated for many strategies.

**Why:** Strategy search reuses the same condition atoms across candidates;
re-running CTL on identical conditions is redundant.

**How:**

- Memoryless: matrix pruning + `_condition_cache` (`NatATL/Memoryless/`,
  `LTL/pruning.py`).
- Recall: tree pruning + `ctl_model_checking_cached`
  (`NatATL/Recall/condition_cache.py`).
- NatSL: uses its shared bounded-strategy core with exact action pruning; inadmissible strategies are rejected instead of receiving an implicit idle-action fallback.

**Advantage:** Cuts repeated CTL checks inside strategy enumeration.

## Performance Regression Tests

**What:** Timed checks on synthetic models (often 100-200 states for ATL/CTL;
larger in scalability suites).

**Why:** Guard against accidental slowdowns when changing pre-image, caches,
or fixpoints.

**How:** `model_checker/tests/performance/` (for example
`test_atl_performance.py`).

**Advantage:** CI signal for runtime regressions. These bounds are not formal
complexity claims and do not define when caches or bit vectors apply.
