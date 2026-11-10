# LTL - Algorithm Reference

Scope: denotations and code path for LTL in
`model_checker/algorithms/explicit/LTL/`.

## Model

- Type: `CGS`
- Checking is strategy-based over concurrent games, not classical path-LTL on a
  single unreduced trace.

## Formula language

Parser: `parsers/formulas/LTL/parser.py`

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi
      | X phi | F phi | G phi | phi U psi
```

User formulas must not contain `E` / `A` or coalitions. `R` / `W` are not in the
surface syntax.

An operator is followed by a space, `(` or `!`: `X p`, `F G p`. `Xp` and `FGp` are
names, and so is `pUq`: write `p U q`. A name that is not among the model's
declared propositions is an error that names it, so see
[operators and names](../logic_knowledge_base.md#operators-and-names) when a name you
did not mean to declare appears in the message.

## Semantic denotations

1. Enumerate natural strategies (default complexity bound `k=5` for the grand
   coalition).
2. Prune the CGS by the strategy profile.
3. Rewrite the formula to an A-prefixed CTL-shaped form (`ltl_to_ctl`) and check
   sure-win on the pruned model.

The rewrite is a parsing bridge, not a semantics-preserving embedding of LTL
into CTL. It is built from the parsed formula, so `p U q U r` (which groups to the
right) becomes `A(p U A(q U r))`.

Implementation techniques (strategy pruning, condition cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Classical path-LTL | Implementation |
|---|---|---|
| Semantics | Paths of the Kripke structure | Sure-win / strategy over CGS |
| Quantifiers | None | Injected `A` after rewrite |
| Operators | X, F, G, U, R, W | `X`, `F`, `G`, `U` only |
| Bound | N/A | Default strategy complexity `k=5` |

## Model-checking pipeline

```text
CGS.read_file -> LTLParser.parse -> strategy prune -> CTL-shaped check
  -> result dict
```

Entry: `LTL/LTL.py`.

## Code map

| Path | Role |
|---|---|
| `LTL/LTL.py` | Entry |
| `LTL/strategies.py` | Strategy enumeration |
| `LTL/pruning.py` | CGS pruning under strategies |

## Tests

Coverage under `model_checker/tests/` for LTL parser and algorithm fixtures.
