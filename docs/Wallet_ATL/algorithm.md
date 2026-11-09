# Wallet_ATL - Algorithm Reference

Scope: denotations and code path for Wallet_ATL in
`model_checker/algorithms/explicit/Wallet_ATL/`. Modeling examples:
[usage.md](usage.md).

## Model

- Type: `WalletCGS`
- Per-state wallet balances in the `Wallets` section.

## Formula language

Parser: `parsers/formulas/Wallet_ATL/parser.py`

```text
phi ::= <<A>> X phi | <<A>> F phi | <<A>> G phi | <<A>> phi U psi | <<A>> (phi U psi)
      | <<A:wallet(agent, op, value)>> ...
```

`<<A>> phi U psi` and `<<A>> (phi U psi)` build the same tree (see
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)).

The `<<...>>` prefix is mandatory before temporal operators. Empty `<<>>` is
invalid.

## Semantic denotations

ATL-style coalition modalities with wallet guards applied as a static filter on
state names that currently satisfy the guard from the `Wallets` section. Guards
do not yet recompute balances along deposit/spend transitions.

Implementation techniques (transition cache, early-stop, ATL prefilter): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Coalition syntax | Wallet-aware | Dedicated `<<...>>` (avoids clash with `<A><k>`) |
| Wallet dynamics | May track spend/deposit | Static balance filter today |
| Temporal ops | X, F, G, U | Same |

## Model-checking pipeline

```text
WalletCGS.read_file -> Wallet_ATLParser.parse -> build_tree
  -> solve_tree -> result
```

Entry: `Wallet_ATL/Wallet_ATL.py`.

## Code map

| Path | Role |
|---|---|
| `Wallet_ATL/Wallet_ATL.py` | Entry |
| `Wallet_ATL/solver.py` | Dispatch |
| `Wallet_ATL/operators.py` | Operators |
| `Wallet_ATL/preimage.py` | Wallet-aware pre-image |

## Tests

WalletCGS unit tests and Wallet_ATL algorithm coverage under
`model_checker/tests/`.
