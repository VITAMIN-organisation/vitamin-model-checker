# ATL* algorithm reference

This page covers the semantics and code path of the ATL*
checker in `model_checker/algorithms/explicit/ATL_STAR/`, for a developer reading
or changing it; the syntax is in the
[syntax cards](../reference/logic_knowledge_base.md#syntax-cards) and the model file format
in [CGS sections](../reference/file_formats.md#cgs-sections).

## Model

- Type: `CGS`, the same as ATL; ATL* adds no new game-structure type.

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

ATL writes a coalition with single angle brackets (`<1,2>`). ATL* writes it with
`<<A>>`, which scopes over a nested path formula; Wallet_ATL uses the same brackets
with a different meaning ([Wallet_ATL](../reference/logic_knowledge_base.md#wallet_atl)).

### Until under a coalition

Table 1 lists the written forms of an Until under a coalition:

**Table 1: Until under an ATL* coalition.**

| Form | Reading |
| :--- | :--- |
| `<<A>> x U y` | The coalition covers the Until: the same tree as `<<A>> (x U y)` |
| `<<A>> (x U y)` | The coalition covers the Until |
| `(<<A>> x) U y` | The coalition covers only the left operand; it is a path formula, so it is checkable only inside another coalition, as in `<<B>> ((<<A>> x) U y)` |

The reading of `<<A>> x U y` comes from the paper that defines ATL (Alur,
Henzinger, Kupferman, JACM 49(5), 2002). The paper writes the ATL formula
`<<A>>phi1 U phi2` for the coalition over the Until, and defines ATL as the
fragment of ATL* in which every temporal operator is immediately preceded by a path
quantifier, so the ATL formula keeps its meaning in ATL*. The paper also says ATL*
formulas are the state formulas, and `(<<A>> x) U y` is only a path formula.

Each operand of that `U` is one unary formula, so `<<1>> X p U q` is
`<<1>> ((X p) U q)` and `X <<1>> p U q` is `X (<<1>> (p U q))`.

### Precedence and ambiguity

`!`, `X`, `F` and `G` bind tighter than the connectives, as the ATL paper reads the
winning condition $\Box\Diamond \mathit{done} \to \psi$:
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

## Semantic denotations

ATL* is not computed as a coalition pre-image fixpoint, unlike every other logic
here. It is reduced to a 2-player parity game in the steps of Table 2:

**Table 2: ATL* reduction to a parity game.**

| Step | What |
| :---: | :--- |
| 1 | Eliminate nested `<<A'>> psi'` bottom-up into fresh propositions |
| 2 | Translate the remaining pure-LTL `psi` to a deterministic parity automaton |
| 3 | Product with the CGS, unfold into a turn-based arena, solve as parity/Büchi/co-Büchi |
| 4 | The truth set of `<<A>> psi` is player 0's winning region |

Steps 2 and 3 need `model_checker/automata/` (vendored, wraps Spot); no other logic
here depends on it. See [Requires Spot](#requires-spot).

## Theory vs implementation

Table 3 sets the usual theory beside this implementation:

**Table 3: ATL* theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Empty coalition | Literature may allow | Rejected (parse error) |
| Unknown atom | Semantics typically leaves undefined | Rejected (semantic error), never silently false |
| Strategy synthesis | Part of ATL*'s semantics | Separate `synthesize_strategy` entry point, not in `model_checking`'s result dict; only a single, non-nested coalition formula |
| Cost | ATL* model checking is 2EXPTIME-complete (JACM 2002, Theorem 5.6) | Same worst case: the LTL to deterministic parity translation is doubly exponential in formula size |

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
| `ATL_STAR/strategy_export.py` | `export_strategy`: the coalition's winning strategy as a JSON-serializable dict, for `synthesize_strategy` |
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
