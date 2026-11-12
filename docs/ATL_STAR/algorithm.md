# ATL* algorithm reference

This page covers the semantics, strategy synthesis and code path of the ATL*
checker in `model_checker/algorithms/explicit/ATL_STAR/`, for a developer reading
or changing it; the syntax is in the
[syntax cards](../logic_knowledge_base.md#syntax-cards) and the model file format
in [CGS sections](../file_formats.md#cgs-sections). The checker runs on `CGS`
models, the same type as ATL; ATL* adds no new game-structure type.

## Formula language

The parser is `parsers/formulas/ATL_STAR/parser.py`, wrapping a hand-written
recursive-descent grammar (`grammar.py`), not PLY, since a coalition can scope over
an arbitrarily nested path formula, unlike ATL.

### Grammar

A state formula `phi` holds at a state; a path formula `psi`, such as a bare
Until, holds on a path:

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi | <<A>> psi
psi ::= phi | !psi | psi && psi | X psi | psi U psi | F psi | G psi | <<A>> psi
```

A coalition is written `<<1,2>>`, and agent ids must be in `1..n`. Unlike ATL,
`<<A>>` may appear anywhere inside a path formula, not just at the root.

ATL writes a coalition with single angle brackets (`<1,2>`). ATL*'s `<<A>>` scopes
over a nested path formula: the same brackets as in
[Wallet_ATL](../logic_knowledge_base.md#wallet_atl), a different operator.

### Until under a coalition

Table 1 lists the written forms of an Until under a coalition:

**Table 1: Until under an ATL* coalition.**

| Form | Reading |
| :--- | :--- |
| `<<A>> x U y` | The coalition covers the Until: the same tree as `<<A>> (x U y)` |
| `<<A>> (x U y)` | The coalition covers the Until |
| `(<<A>> x) U y` | The coalition covers only the left operand; it is a path formula, so it is checkable only inside another coalition, as in `<<B>> ((<<A>> x) U y)` |

The reading of `<<A>> x U y` comes from the paper that defines ATL (Alur,
Henzinger, Kupferman, JACM 49(5), 2002). Section 3.1 (p. 685) writes the ATL
formula `<<A>>phi1 U phi2` for the coalition over the Until. Section 3.4 (p. 689)
defines ATL as the fragment of ATL* in which every temporal operator is
immediately preceded by a path quantifier, so the ATL formula keeps its meaning in
ATL*. The same section says ATL* formulas are the state formulas, and
`(<<A>> x) U y` is only a path formula.

Each operand of that `U` is one unary formula, so `<<1>> X p U q` is
`<<1>> ((X p) U q)` and `X <<1>> p U q` is `X (<<1>> (p U q))`.

### Precedence and ambiguity

`!`, `X`, `F` and `G` bind tighter than the connectives, as the paper reads the
winning condition $\Box\Diamond \mathit{done} \to \psi$ (p. 693):
`<<1>> (F p && G q)` is `<<1>> ((F p) && (G q))`.

The paper states no precedence rule for the rest, so these are syntax errors that
ask for parentheses:

- A second `U`, as in `<<1>> p U q U r` or `p U q U r`.
- `U` next to `&&`, `||` or `->`, as in `p U q && r` or `p && q U r`. The message is
  `'x U y && z' is ambiguous: write (x U y) && z or x U (y && z)`, with the
  position of the `U`.
- A connective right after a coalition, as in `<<1>> p && q`, `<<1>> F p && q` or
  `<<1>> (p U q) && r`. In ATL, `<1> p` is no formula, but in ATL* a coalition can
  scope over any path formula, so `<<1>> p && q` is `(<<1>> p) && q` or
  `<<1>> (p && q)`. Write `(<<1>> F p) && q` or `<<1>> (F p && q)`. A coalition at the
  end, `q && <<1>> F p`, has one reading.

## Semantic approach

ATL* is not computed as a coalition pre-image fixpoint, unlike every other logic
here. It is reduced to a 2-player parity game in the steps of Table 2:

**Table 2: ATL* reduction to a parity game.**

| Step | What |
| :---: | :--- |
| 1 | Eliminate nested `<<A'>> psi'` bottom-up into fresh propositions |
| 2 | Translate the remaining pure-LTL `psi` to a deterministic parity automaton |
| 3 | Product with the CGS, unfold into a turn-based arena, solve as parity/Büchi/co-Büchi |
| 4 | `<<A>> psi`'s truth set = player 0's winning region |

Steps 2 and 3 need `model_checker/automata/` (vendored, wraps Spot); no other logic
here depends on it. See [Requires Spot](#requires-spot).

## Model-checking pipeline

The checker reads the model, parses the formula, adapts the model, solves and formats the result:

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#1f5f99", "primaryTextColor": "#ffffff", "primaryBorderColor": "#4a90d9", "lineColor": "#75808f", "tertiaryTextColor": "#75808f", "titleColor": "#75808f", "clusterBkg": "transparent", "clusterBorder": "#75808f", "edgeLabelBackground": "transparent"}}}%%
flowchart LR
    load["CGS.read_file"]
    parse["ATLStarParser.parse"]
    adapt["cgs_adapter.adapt"]
    sat["verifier.sat"]
    result["format_model_checking_result"]

    load --> parse --> adapt --> sat --> result
```

## Theory vs implementation

Table 3 sets the usual theory beside this implementation:

**Table 3: ATL* theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Empty coalition | Literature may allow | Rejected (parse error) |
| Unknown atom | Semantics typically leaves undefined | Rejected (semantic error), never silently false |
| Strategy synthesis | Part of ATL*'s semantics | Separate `synthesize_strategy` entry point, not in `model_checking`'s result dict; only a single, non-nested coalition formula |

## Cost of model checking

Two separate things grow: formula-to-DPA translation is
exponential in formula size in the worst case, model-independent. At
realistic model sizes, the explicit-state product/arena construction here
(not Spot's own game solver) tends to dominate wall time.

## Strategy synthesis is a separate entry point

`ATL_STAR.model_checking`'s result dict is the usual satisfaction dict
(satisfying states, whether the initial state holds), same as every other
logic here. It does not return a strategy.

A second, separate entry point returns one instead:
`ATL_STAR.synthesize_strategy(formula, filename, state=None)`. It gives a
JSON-serializable dict with the same `res`, `initial_state` and `error`
conventions as `model_checking`:

```text
{"satisfied": bool,
 "strategy": {"start": ..., "moves": [...], "transitions": [...]} | None,
 ...}
```

It is meant to be imported and called directly by a consumer that specifically
wants a strategy, not dispatched through the generic `vitamin.benchmarks`
entry-point registry (which only knows the fixed two-argument `model_checking`
shape).

`strategy["start"]` is the `(state, memory)` position to begin from. `memory` is
the underlying automaton's own state number, tracking how much of the temporal
formula has already been satisfied along the run so far (e.g. whether the left
side of a `U` already held). It is the bookkeeping the strategy needs and has no
counterpart in the CGS.

`strategy["moves"]` lists the coalition's own action at every position reachable
from `start`. `strategy["transitions"]` lists, for each such position, every real
successor consistent with that move (more than one when the rest of the system is
still free to respond differently), each tagged with the full joint action that
leads there.

A consumer replays a run by starting at `start`, reading the coalition's move for
the current position from `moves`, and once it observes what actually happened,
finding the matching row in `transitions` to know the next position.

Only a formula whose outermost operator is a single coalition with no further
coalition nested inside its path formula is supported
(`verifier.require_simple_coalition`). A top-level boolean combination of
coalitions (`(<<1>> F p) && (<<2>> G q)`) or a nested one (`<<1>> G <<2>> F p`)
comes back as a "semantic" error instead. Both would need more than one
independent strategy to represent faithfully, so broader formulas are not
supported.

For the general case (nested coalitions included),
`verifier.witness(formula, model, state)` still returns the full `Witness`,
including nested witnesses via `Witness.nested_witnesses_at`.
`strategy_export.export_strategy` only flattens the coalition's own, top-level
strategy to JSON and leaves out the nested part.

## Requires Spot

The Spot team publishes no official PyPI wheel. On Linux, the community
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

## Code map

Table 4 lists the files of the checker and their role:

**Table 4: ATL* code map.**

| Path | Role |
| :--- | :--- |
| `ATL_STAR/ATL_STAR.py` | Entry |
| `ATL_STAR/verifier.py` | Bottom-up elimination, LTL rendering, game construction/solving, formula-shape validation |
| `ATL_STAR/cgs_adapter.py` | CGS to `TransitionSystem` adapter |
| `ATL_STAR/strategy_export.py` | Flattens a `Witness` into a JSON-serializable `start`/`moves`/`transitions` dict (`export_strategy`) |
| `parsers/formulas/ATL_STAR/grammar.py` | Tokenizer/recursive-descent parser |
| `parsers/formulas/ATL_STAR/formula.py` | Formula AST |
| `model_checker/automata/` | Vendored `automata_mc`: `Automaton`, `product`, `complete`, `concurrent_to_turnbased`, `solve` |

## Tests

Table 5 lists the test paths, relative to the repository root:

**Table 5: ATL* tests.**

| Path | Coverage |
| :--- | :--- |
| `model_checker/tests/unit/algorithms/atl_star/` | Adapter, verifier, end-to-end |
| `model_checker/tests/unit/parsers/formulas/test_atl_star_parser.py` | Parser |
| `model_checker/tests/integration/algorithms/atl_star/test_semantics.py` | Semantics |
| `model_checker/tests/integration/algorithms/atl_star/test_strategy_synthesis.py` | Strategy synthesis |
| `model_checker/tests/unit/automata/` | The vendored `automata_mc`'s own suite |
