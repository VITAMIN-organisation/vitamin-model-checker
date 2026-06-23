# Wallet_ATL

Wallet_ATL extends standard ATL with per-agent wallet balances. Coalitions can
include wallet constraints on which strategies are feasible.

## Model type

Uses `WalletCGS` - a CGS plus a `Wallets` section. See
[File Formats](../file_formats.md#walletcgs-sections).

## Formula syntax

Coalitions use double angle brackets. Optional wallet guards come after `:`.

```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50) && wallet(2, <= 100)>>G safe
```

Temporal operators: `X`, `F`, `G`, `U`. Every temporal formula must begin with a `<<>>` coalition prefix.

Wallet guards use `wallet(agent, operator, value)` where operator is
`>=`, `<=`, `>`, `<`, or `==`.
