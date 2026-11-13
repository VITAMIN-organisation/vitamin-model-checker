# Wallet_ATL algorithm

The Wallet_ATL checker decides `<<A:C>> phi`: can coalition `A` force `phi` using
only moves every agent can pay for, while the balance guards `C` hold where `A`
moves? It runs on a `WalletCGS` model, where each state gives each agent a wallet
balance. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#wallet_atl), the model file
in [WalletCGS sections](../reference/file_formats.md#walletcgs-sections), and
modelling examples in [Wallet_ATL usage](../examples/wallet_atl_usage.md).

## Payable moves

Before any operator runs, the checker removes every joint move that some agent
cannot pay for in the state where it starts. Each agent's action is one of three
kinds:

- Consumption: `D`, `B`, `S`, `T` or `N` followed by an amount, as in `D20`. It is
  payable only if the agent's balance in that state is at least the amount.
- Income: `W`, `R`, `E`, `F` or `U` followed by an amount, as in `W20`. Always
  payable.
- Neutral: any other token, such as `I`, `0`, `*`, or a consumption letter with no
  amount. Always payable.

Every agent's action is checked, not only the coalition's. A state left with no
payable move is an error that names the state. Balances are read from the
`Wallets` section and never change along a path: paying `D20` does not lower the
balance of the next state.

## Operators

`Pre(Z)` is the ATL [pre-image](index.md#overview) (see
[ATL](atl.md#coalition-pre-image)) over payable moves.
`Guard` is the set of states where every guard in `C` holds, each guard comparing
an agent's balance in that state with a number (all states when `C` is empty).
Each step of an operator is `Step(Z) = Pre(Z) & Guard`; `[[phi]]` is the set of
states where `phi` holds. Fixpoints are defined in the
[overview](index.md#overview).

**Table 1: Wallet_ATL operators.**

| Formula | Set computed | Iteration starts from |
| :--- | :--- | :--- |
| `<<A:C>> X phi` | `Step([[phi]])` | (no iteration) |
| `<<A:C>> G phi` | greatest fixpoint of `Z = Step(Z) & [[phi]]` | all states |
| `<<A:C>> (phi U psi)` | least fixpoint of `Z = Z \| (Step(Z) & [[phi]])` | `[[psi]]` |
| `<<A:C>> F phi` | as `<<A:C>> (true U phi)` | `[[phi]]` |

The guard is checked in the state where the coalition moves, on every round of the
fixpoint, but not in the target: a state in `[[psi]]` (or `[[phi]]` for `F`) is
in the result even where the guard fails, and `X` does not check the guard in
the next state. A state where the guard fails is not in the result of `X` or `G`.

Example: two agents; in `s0` agent 1 can play `I` (stay in `s0`) or `D20` (go to
`s1`, where `q` holds). Table 2 lists the results:

**Table 2: Wallet_ATL results on the example.**

| Balance of agent 1 in `s0` | Formula | Result |
| :---: | :--- | :--- |
| 10 | `<<1>> F q` | `{s1}`: `D20` is not payable |
| 30 | `<<1>> F q` | `{s0, s1}` |
| 30 | `<<1:wallet(1, >= 40)>> F q` | `{s1}`: the guard fails in `s0` |
| 30 | `<<1:wallet(1, >= 20)>> F q` | `{s0, s1}` |
