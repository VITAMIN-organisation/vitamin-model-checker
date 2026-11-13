# Wallet_ATL usage

This page is for a user starting with Wallet_ATL: it names the model type and
gives two example formulas, with links to the full rules. Wallet_ATL extends
standard ATL with per-agent wallet balances. A joint move is kept only if every
agent can pay for its action
([payable moves](../algorithms/wallet_atl.md#payable-moves)), and a coalition
can add wallet guards, conditions on balances in the states where it moves
([operators](../algorithms/wallet_atl.md#operators) says where each operator
checks them).

## Model type

A Wallet_ATL model is a `WalletCGS`: a CGS (concurrent game structure) plus a
`Wallets` section. See
[WalletCGS sections](../reference/file_formats.md#walletcgs-sections).

## Formula syntax

Coalitions use double angle brackets. Optional wallet guards come after `:`.
In these examples, `auction_active` and `safe` are example proposition names:

```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50) && wallet(2, <= 100)>>G safe
```

The temporal operators are `X`, `F`, `G` and `U`. The guard form and its rules
are in the [knowledge base](../reference/logic_knowledge_base.md#wallet_atl).
