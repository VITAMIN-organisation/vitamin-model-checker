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
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi | <<A>> psi
psi ::= phi | !psi | psi && psi | X psi | psi U psi | F psi | G psi | <<A>> psi
```

Coalition form: `<<1,2>>`. Agent ids must be in `1..n`. Unlike ATL, `<<A>>`
may appear anywhere inside a path formula, not just at the root.

Written forms of an Until under a coalition:

| Form | Reading |
| :--- | :--- |
| `<<A>> x U y` | The coalition covers the Until: the same tree as `<<A>> (x U y)`. |
| `<<A>> (x U y)` | The coalition covers the Until. |
| `(<<A>> x) U y` | The coalition covers only the left operand. It is a path formula, so it is checkable only inside another coalition, as in `<<B>> ((<<A>> x) U y)`. |

The reading of `<<A>> x U y` comes from the paper that defines ATL (Alur,
Henzinger, Kupferman, JACM 49(5), 2002). Section 3.1 (p. 685) writes the ATL
formula `<<A>>phi1 U phi2` for the coalition over the Until. Section 3.4 (p. 689)
defines ATL as the fragment of ATL* in which every temporal operator is
immediately preceded by a path quantifier, so the ATL formula keeps its meaning in
ATL*. The same section says ATL* formulas are the state formulas (a state formula
holds at a state; a path formula, such as a bare Until, holds on a path), and
`(<<A>> x) U y` is only a path formula.

Each operand of that `U` is one unary formula, so `<<1>> X p U q` is
`<<1>> ((X p) U q)` and `X <<1>> p U q` is `X (<<1>> (p U q))`.

The paper states no precedence rule, so these are syntax errors that ask for
parentheses:

- A second `U`, as in `<<1>> p U q U r` or `p U q U r`.
- `U` next to `&&`, `||` or `->`, as in `p U q && r` or `p && q U r`. The message is
  `'x U y && z' is ambiguous: write (x U y) && z or x U (y && z)`, with the
  position of the `U`.
- A connective right after a coalition, as in `<<1>> p && q`, `<<1>> F p && q` or
  `<<1>> (p U q) && r`. In ATL, `<1> p` is no formula, but in ATL* a coalition can
  scope over any path formula, so `<<1>> p && q` is `(<<1>> p) && q` or
  `<<1>> (p && q)`. Write `(<<1>> F p) && q` or `<<1>> (F p && q)`. A coalition at the
  end, `q && <<1>> F p`, has one reading.

`!`, `X`, `F` and `G` bind tighter than the connectives, as the paper reads the
winning condition $\Box\Diamond done \to \psi$ (p. 693):
`<<1>> (F p && G q)` is `<<1>> ((F p) && (G q))`.

ATL writes a coalition with single angle brackets (`<1,2>`). Wallet_ATL also writes
`<<...>>`, to avoid a clash with NatATL's `<k>` bound notation, and allows a
`:wallet(agent, op, value)` guard inside. ATL*'s `<<A>>` scopes over a nested path
formula: the same brackets, a different operator.

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
| Strategy synthesis | Part of ATL*'s semantics | Separate `synthesize_strategy` entry point, not in `model_checking`'s result dict; only a single, non-nested coalition formula |

## Cost

Two separate sources of blow-up, not one: formula-to-DPA translation is
exponential in formula size in the worst case, model-independent. At
realistic model sizes, the explicit-state product/arena construction here
(not Spot's own game solver) tends to dominate wall time.

## Requires Spot

No official PyPI wheel from the Spot team. On Linux, the community
[`spottl`](https://pypi.org/project/spottl/) package gives one anyway
(imports as `spot`), and is installed automatically as a regular
dependency of `vitamin-model-checker` on that platform, no separate step
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

## Strategy synthesis is a separate entry point

`ATL_STAR.model_checking`'s result dict is the usual satisfaction dict
(satisfying states, whether the initial state holds), same as every other
logic here. It does not return a strategy, kept that way deliberately, so
this entry point stays focused on plain model checking.

A second, separate entry point, `ATL_STAR.synthesize_strategy(formula,
filename, state=None)`, returns one instead, as a JSON-serializable dict
(`{"satisfied": bool, "strategy": {"start": ..., "moves": [...],
"transitions": [...]} | None, ...}`, same `res`/`initial_state`/`error`
conventions as `model_checking`), meant to be imported and called
directly by a consumer that specifically wants a strategy, not dispatched
through the generic `vitamin.benchmarks` entry-point registry (which only
knows the fixed two-argument `model_checking` shape).

`strategy["start"]` is the `(state, memory)` position to begin from.
`memory` is the underlying automaton's own state number, tracking how
much of the temporal formula has already been satisfied along the run so
far (e.g. whether an `U`'s left side already held), not a CGS concept,
just the bookkeeping the strategy needs. `strategy["moves"]` lists the
coalition's own action at every position reachable from `start`.
`strategy["transitions"]` lists, for each such position, every real
successor consistent with that move (more than one when the rest of the
system is still free to respond differently), each tagged with the full
joint action that leads there. A consumer replays a run by starting at
`start`, reading the coalition's move for the current position from
`moves`, and once it observes what actually happened, finding the
matching row in `transitions` to know the next position.

Only supports a formula whose outermost operator is a single coalition
with no further coalition nested inside its path formula
(`verifier.require_simple_coalition`), a top-level boolean combination of
coalitions (`(<<1>> F p) && (<<2>> G q)`) or a nested one
(`<<1>> G <<2>> F p`) comes back as a "semantic" error instead. Both would
need more than one independent strategy to represent faithfully; broader
support is deferred to a later iteration.

For the general case (nested coalitions included), `verifier.witness(formula,
model, state)` still returns the full `Witness`, including nested witnesses
via `Witness.nested_witnesses_at`. `strategy_export.export_strategy` only
flattens the coalition's own, top-level strategy to JSON, deliberately not
the nested part yet.

## Code map

| Path | Role |
|---|---|
| `ATL_STAR/ATL_STAR.py` | Entry |
| `ATL_STAR/verifier.py` | Bottom-up elimination, LTL rendering, game construction/solving, formula-shape validation |
| `ATL_STAR/cgs_adapter.py` | CGS to `TransitionSystem` adapter |
| `ATL_STAR/strategy_export.py` | Flattens a `Witness` into a JSON-serializable `start`/`moves`/`transitions` dict (`export_strategy`) |
| `parsers/formulas/ATL_STAR/grammar.py` | Tokenizer/recursive-descent parser |
| `parsers/formulas/ATL_STAR/formula.py` | Formula AST |
| `model_checker/automata/` | Vendored `automata_mc`: `Automaton`, `product`, `complete`, `concurrent_to_turnbased`, `solve` |

## Tests

- `model_checker/tests/unit/algorithms/atl_star/` (adapter, verifier, end-to-end)
- `model_checker/tests/unit/parsers/formulas/test_atl_star_parser.py`
- `model_checker/tests/integration/algorithms/atl_star/test_semantics.py`
- `model_checker/tests/integration/algorithms/atl_star/test_strategy_synthesis.py`
- `model_checker/tests/unit/automata/` (the vendored `automata_mc`'s own suite)
