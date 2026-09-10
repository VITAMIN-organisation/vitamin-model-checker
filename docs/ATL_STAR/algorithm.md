# ATL* - Algorithm Reference

Scope: denotations and code path for ATL* in
`model_checker/algorithms/explicit/ATL_STAR/`.

## Model

- Type: `CGS` (same as ATL, no new game-structure type)

## Formula language

Parser: `parsers/formulas/ATL_STAR/parser.py`, wrapping a hand-written
recursive-descent grammar (`grammar.py`) — not PLY, since a coalition can
scope over an arbitrarily nested path formula, unlike ATL.

```text
phi ::= p | !phi | phi & psi | phi | psi | phi -> psi | <<A>> psi
psi ::= phi | !psi | psi & psi | X psi | psi U psi | F psi | G psi | <<A>> psi
```

Coalition form: `<<1,2>>`. Agent ids must be in `1..n`. Unlike ATL, `<<A>>`
may appear anywhere inside a path formula, not just at the root.

## Semantic approach

Not a coalition pre-image fixpoint (unlike every other logic here) —
reduced to a 2-player parity game:

| Step | What |
|---|---|
| 1 | Eliminate nested `<<A'>> psi'` bottom-up into fresh propositions |
| 2 | Translate the remaining pure-LTL `psi` to a deterministic parity automaton |
| 3 | Product with the CGS, unfold into a turn-based arena, solve as parity/Büchi/co-Büchi |
| 4 | `<<A>> psi`'s truth set = player 0's winning region |

Needs `model_checker/automata/` (vendored, wraps Spot) — no other logic
here depends on it.

## Requires Spot (conda-forge only, not pip)

```bash
conda install -c conda-forge spot
```

No PyPI wheel exists. The rest of VITAMIN works without it; a missing
Spot returns an `"environment"`-type error instead of crashing on import.

## Model-checking pipeline

```text
CGS.read_file -> ATLStarParser.parse -> cgs_adapter.adapt -> verifier.sat
  -> format_model_checking_result
```
