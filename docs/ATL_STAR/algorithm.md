# ATL* - Algorithm Reference

Scope: denotations and code path for ATL* in
`model_checker/algorithms/explicit/ATL_STAR/`.

## Model

- Type: `CGS` (same as ATL, no new game-structure type)

## Formula language

Parser: `parsers/formulas/ATL_STAR/parser.py`, wrapping a hand-written
recursive-descent grammar (`grammar.py`), not PLY, since a coalition can
scope over an arbitrarily nested path formula, unlike ATL.

```text
phi ::= p | !phi | phi & psi | phi | psi | phi -> psi | <<A>> psi
psi ::= phi | !psi | psi & psi | X psi | psi U psi | F psi | G psi | <<A>> psi
```

Coalition form: `<<1,2>>`. Agent ids must be in `1..n`. Unlike ATL, `<<A>>`
may appear anywhere inside a path formula, not just at the root.

**Not the same syntax as other `<<...>>` users in this codebase**: ATL uses
single angle brackets (`<1,2>`); Wallet_ATL also uses `<<...>>` but for a
different reason (avoiding a clash with NatATL's `<k>` bound notation) and
allows an optional `:wallet(agent, op, value)` guard inside. ATL*'s `<<A>>`
scopes over an arbitrarily nested path formula, a distinct operator with
distinct semantics, not a shared surface.

## Semantic approach

Not a coalition pre-image fixpoint (unlike every other logic here),
reduced to a 2-player parity game:

| Step | What |
|---|---|
| 1 | Eliminate nested `<<A'>> psi'` bottom-up into fresh propositions |
| 2 | Translate the remaining pure-LTL `psi` to a deterministic parity automaton |
| 3 | Product with the CGS, unfold into a turn-based arena, solve as parity/Büchi/co-Büchi |
| 4 | `<<A>> psi`'s truth set = player 0's winning region |

Needs `model_checker/automata/` (vendored, wraps Spot); no other logic
here depends on it.

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Empty coalition | Literature may allow | Rejected (parse error) |
| Unknown atom | Semantics typically leaves undefined | Rejected (semantic error), never silently false |
| Strategy synthesis | Part of ATL*'s semantics | `verifier.witness(...)` only, not in `model_checking`'s result dict |

## Cost

Two separate sources of blow-up, not one: formula-to-DPA translation is
exponential in formula size in the worst case, model-independent. At
realistic model sizes, the explicit-state product/arena construction here
(not Spot's own game solver) tends to dominate wall time.

## Requires Spot

No official PyPI wheel from the Spot team. On Linux, the community
[`spottl`](https://pypi.org/project/spottl/) package gives one anyway
(imports as `spot`), and is installed automatically as a regular
dependency of `vitamin-model-checker` on that platform — no separate step
or extra needed:

```bash
pip install vitamin-model-checker
```

On macOS, or to pin an exact Spot version, use conda-forge instead:

```bash
conda install -c conda-forge spot
```

Neither path has a Windows build; use WSL there. The rest of VITAMIN
works without Spot either way; a missing Spot returns an
`"environment"`-type error instead of crashing on import.

## Model-checking pipeline

```text
CGS.read_file -> ATLStarParser.parse -> cgs_adapter.adapt -> verifier.sat
  -> format_model_checking_result
```

## Strategy synthesis is a verifier-only API

`ATL_STAR.model_checking`'s result dict is the usual satisfaction dict
(satisfying states, whether the initial state holds), same as every other
logic here. It does not return a strategy. Building one requires calling
`verifier.witness(formula, model, state)` directly, a separate API this
module also provides, not something the public entry point exposes.

## Code map

| Path | Role |
|---|---|
| `ATL_STAR/ATL_STAR.py` | Entry |
| `ATL_STAR/verifier.py` | Bottom-up elimination, LTL rendering, game construction/solving |
| `ATL_STAR/cgs_adapter.py` | CGS to `TransitionSystem` adapter |
| `parsers/formulas/ATL_STAR/grammar.py` | Tokenizer/recursive-descent parser |
| `parsers/formulas/ATL_STAR/formula.py` | Formula AST |
| `model_checker/automata/` | Vendored `automata_mc`: `Automaton`, `product`, `complete`, `concurrent_to_turnbased`, `solve` |

## Tests

- `model_checker/tests/unit/algorithms/atl_star/` (adapter, verifier, end-to-end)
- `model_checker/tests/unit/parsers/formulas/test_atl_star_parser.py`
- `model_checker/tests/integration/algorithms/atl_star/test_semantics.py`
- `model_checker/tests/unit/automata/` (the vendored `automata_mc`'s own suite)
