# OL - Algorithm Reference

Scope: denotations and code path for OL in
`model_checker/algorithms/explicit/OL/`.

## Model

- Type: `costCGS`
- Linear-time cost-bounded logic paired with OATL models.

## Formula language

Parser: `parsers/formulas/OL/parser.py`

```text
phi ::= ... | <Jk> X phi | <Jk> F phi | <Jk> G phi
           | <Jk>(phi U psi) | <Jk>(phi R psi) | <Jk>(phi W psi)
```

Prefix must include `J` (`<J5>`). Bound `k >= 1`.

Written forms of `U`, `R` and `W` after the prefix (`U` shown):

| Form | Accepted | Where it comes from |
| :--- | :--- | :--- |
| `<J2> (p U q)` | yes | ECAI 2023, Definition 1 (PDF page 2): $\langle n\rangle(\varphi\ U\ \varphi)$ and $\langle n\rangle(\varphi\ R\ \varphi)$. |
| `<J2> p U q` | yes | The paper's prose writes this form too, $\langle n\rangle\varphi\ U\ \psi$ (PDF page 4). |

`W` is the paper's abbreviation
$\langle n\rangle(\varphi\ W\ \psi) := \langle n\rangle(\psi\ R\ (\varphi \lor \psi))$
and takes both forms. Both forms build the same tree (see
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)).
`<J2> p && q U r` is `<J2> ((p && q) U r)`, its only reading, because `<J2> p`
alone is no formula. The paper states no
precedence rule, so `<J2> p U q && r` and `<J2>F p && q` are syntax errors that
ask for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

| Operator family | Cost meaning |
|---|---|
| `F` / `G` / `U` / `R` / `W` | Accumulated path cost `<= k` |
| `X` | Next transition cost `<= k` |

This differs from OATL, where the budget limits what the Demon erases at each
step, and from TOL (per-position demonic deactivation on timed models).

Shared costCGS techniques: [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Prefix | Demonic / cost bound | `<Jk>` mandatory |
| Path cost | Budget along path | Accumulated for most ops; per-step for `X` |

## Model-checking pipeline

```text
costCGS.read_file -> OLParser.parse -> build_tree -> solve_tree -> result
```

Entry: `OL/OL.py`.

## Code map

| Path | Role |
|---|---|
| `OL/OL.py` | Entry |
| `OL/solver.py` | Dispatch |
| `OL/operators.py` | Operators |
| `OL/preimage.py` | Cost-aware pre-image |

## Tests

OL fixtures and integration tests under `model_checker/tests/`.
