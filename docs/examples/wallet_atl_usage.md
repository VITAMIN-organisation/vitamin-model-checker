# Wallet_ATL

Wallet_ATL extends standard ATL with per-agent wallet balances. A joint move is
kept only if every agent can pay for its action
([payable moves](../algorithms/wallet_atl.md#payable-moves)), and a coalition
can add wallet guards, conditions on balances in the states where it moves
([operators](../algorithms/wallet_atl.md#operators) says where each operator
checks them).

## Model type

Uses `WalletCGS` - a CGS plus a `Wallets` section. See
[File Formats](../reference/file_formats.md#walletcgs-sections).

## Formula syntax

Coalitions use double angle brackets. Optional wallet guards come after `:`.

```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50) && wallet(2, <= 100)>>G safe
```

Temporal operators: `X`, `F`, `G`, `U`. The guard form and its rules (comparison
operators, natural-number values, guard agents in the coalition, `&&` only,
`<<>>` rejected) are in the
[knowledge base](../reference/logic_knowledge_base.md#wallet_atl).
