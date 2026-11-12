# Wallet_ATL algorithm reference

This page gives the algorithm of the Wallet_ATL checker in
`model_checker/algorithms/explicit/Wallet_ATL/` and how it differs from the
paper, for developers reading or changing the checker; the syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#wallet_atl), the model format in
[WalletCGS sections](../reference/file_formats.md#walletcgs-sections) and modeling
examples in [usage.md](../examples/wallet_atl_usage.md).

## Model

- Type: `WalletCGS`
- Per-state wallet balances in the `Wallets` section.

## Formula language

Parser: `parsers/formulas/Wallet_ATL/parser.py`

```text
phi ::= p | true | false | !phi | phi && psi | phi || psi | phi -> psi | (phi)
      | <<A>> X phi | <<A>> F phi | <<A>> G phi | <<A>> phi U psi | <<A>> (phi U psi)
      | <<A:guard && guard && ...>> ...
guard ::= wallet(agent, op value)
```

`<<A>> phi U psi` and `<<A>> (phi U psi)` build the same tree (see
[the knowledge base](../reference/logic_knowledge_base.md#until-after-a-prefix)), and
`<<A>>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../reference/logic_knowledge_base.md#prefix-before-a-connective)).
The `<<...>>` prefix is mandatory before temporal operators, and empty `<<>>` is
invalid.

A guard is written `wallet(agent, op value)`, with `op` one of `>=`, `<=`, `==`,
`>`, `<`, and guards are joined with `&&`, as in
`<<1,2:wallet(1, >= 10) && wallet(2, >= 0)>>`. Every guard must hold, and a
coalition agent with no guard is unconstrained. Each guard names a coalition
agent: `<<1:wallet(2, >= 5)>>` is a syntax error that names agent 2.

## Semantic denotations

Source: "Wallet ATL: Towards Reliable Smart Contract Verification" (AAMAS 2026).

An action token is one of three kinds; a token that is one capital letter
followed by an amount is consumption or income depending on the letter:

- Consumption: `D`, `B`, `S`, `T` or `N` followed by an amount, as in `D20`.
- Income: `W`, `R`, `E`, `F` or `U` followed by an amount, as in `W20`.
- Neutral: every other token, such as `I`, `IDLE`, a number like `0`, or `*`.

A joint move counts only when every agent can pay for its part at the current
state: a consumption action of amount `v` needs at least `v` in the acting
agent's wallet; income and neutral actions are always allowed (the paper's
Def. 3.1 and 4.1). So agent 1 with 5 in the wallet cannot win through a `D20`
move. A state where no transition is payable is an error that names the state,
and so is a state with no row in `Wallets`.

### Operators

In `<<A:C>>...`, `A` is the coalition and `C` the conjunction of its guards.
`Pre(A, S)` is the set of states from which `A` can force the next state into
`S` using payable moves only, `wPre(S)` keeps the states of `S` where every
guard in `C` holds (all of `S` when `C` is empty), and `rho` is the set built so
far in a fixpoint. Table 1 lists how each operator is computed:

**Table 1: Wallet_ATL operators and the lines of the paper's Algorithm 1 they follow.**

| Formula | Computed as | Paper |
| :--- | :--- | :--- |
| `<<A:C>>X phi` | `wPre(Pre(A, [[phi]]))` | Algorithm 1 line 9 |
| `<<A:C>>G phi` | from all states, repeat: `rho` becomes `wPre(Pre(A, rho))` intersected with `[[phi]]` | Algorithm 1 lines 10-17 |
| `<<A:C>>phi U psi` | from `[[psi]]`, repeat: add `wPre(Pre(A, rho))` intersected with `[[phi]]` | Algorithm 1 lines 18-25 |
| `<<A:C>>F psi` | `<<A:C>>true U psi` | not in the paper's grammar |

For example, take s0 with 10 in agent 1's wallet, whose only move leads to s1
with 5, where `goal` holds. With `C = wallet(1, >= 10)`, `<<1:C>>X goal` holds
at s0: the guard is checked where the move starts, not at the next state.
`<<1:C>>F goal` holds at s0 and at s1.

Implementation techniques (transition cache, early-stop): [algorithm design](index.md).

## Theory vs implementation

Where the paper is silent or gives two answers, the code follows Algorithm 1.
Table 2 sets the paper next to the code:

**Table 2: Wallet_ATL theory and implementation.**

| Aspect | Paper | Code |
| :--- | :--- | :--- |
| Coalition syntax | Wallet-aware coalition | Dedicated `<<...>>`, distinct from the OATL/RBATL prefix `<A><k>` |
| Guard on a non-coalition agent | Allowed by the grammar; Def. 4.5 and Algorithm 1 use coalition agents only | Syntax error |
| Several guards on one agent | One bound per agent | Allowed (`wallet(1, >= 3) && wallet(1, <= 5)`), read as a conjunction |
| Wallet predicate as a formula | `wallet(a, op v)` is a state formula, for any agent | Only as a guard inside `<<A:...>>` |
| Temporal operators | X, U, G | X, U, G, and F as `true U` |
| Where the guard is checked | Def. 4.5: first state of the path; Algorithm 1: every round of G and U | Every round (Algorithm 1) |
| Start set of U and F | Algorithm 1 line 20: `[[psi]]` with no guard; prose: "provided all wallet constraints are satisfied" | `[[psi]]` with no guard, so `<<A:C>>X psi` implies `<<A:C>>F psi` |
| State where the guard fails | Def. 4.5 read literally: true by vacuity; Algorithm 1 and prose: false | False |
| G when `phi` holds everywhere | Algorithm 1 skips the loop and returns all states | `wPre` in every round, as in the other cases |
| Balance updates | Def. 4.4: the acting agent's wallet changes; Example 3.3: the amount also moves to or from the contract | Balances read from `Wallets`, never updated along transitions |
| Consumption letter with no amount (`D`) | Amounts are positive integers (Def. 3.1) | Neutral action |

## Code map

Table 3 lists the files of the checker; paths are relative to
`model_checker/algorithms/explicit/`.

**Table 3: Wallet_ATL code map.**

| Path | Role |
| :--- | :--- |
| `Wallet_ATL/Wallet_ATL.py` | Entry |
| `Wallet_ATL/solver.py` | Dispatch |
| `Wallet_ATL/operators.py` | Operators |
| `Wallet_ATL/preimage.py` | Wallet-aware pre-image |

## Tests

WalletCGS unit tests and Wallet_ATL algorithm coverage under
`model_checker/tests/`.
