# LTL algorithm reference

This page covers the denotations and code path of the LTL checker in
`model_checker/algorithms/explicit/LTL/`, for a developer reading or changing it;
the syntax is in the [syntax cards](../logic_knowledge_base.md#syntax-cards) and
the model file format in [CGS sections](../file_formats.md#cgs-sections).

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
syntax errors: a name starts with a lowercase letter, so `Xp` is neither a name nor
`X` applied to `p`. `pUq` is read as one name; write `p U q` for the Until (see
[operators glued to a name](../logic_knowledge_base.md#operators-glued-to-a-name)). A name that is not among the model's
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

Table 1 sets classical path-LTL beside this implementation.

**Table 1: LTL theory and implementation.**

| Aspect | Classical path-LTL | Implementation |
| :--- | :--- | :--- |
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

Table 2 lists the files of the checker and their role.

**Table 2: LTL code map.**

| Path | Role |
| :--- | :--- |
| `LTL/LTL.py` | Entry |
| `LTL/strategies.py` | Strategy enumeration |
| `LTL/pruning.py` | CGS pruning under strategies |

## Tests

Coverage under `model_checker/tests/` for LTL parser and algorithm fixtures.
