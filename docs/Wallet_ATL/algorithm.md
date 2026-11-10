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
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)), and
`<<A>>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

The `<<...>>` prefix is mandatory before temporal operators. Empty `<<>>` is
invalid.

## Semantic denotations

Source: the paper that defines the logic, "Wallet ATL: Towards Reliable Smart
Contract Verification" (AAMAS 2026; kept locally as `docs/papers/AAMAS26b.pdf`,
which git does not track).

An action token is one of three kinds:

- Consumption: `D`, `B`, `S`, `T` or `N` followed by an amount, as in `D20`.
- Income: `W`, `R`, `E`, `F` or `U` followed by an amount, as in `W20`.
- Neutral: every other token, such as `I`, `IDLE`, a number like `0`, or `*`.

A joint move (one action per agent) counts only when every agent can take its
part at the current state. A consumption action of amount `v` needs at least `v`
in the acting agent's wallet there; income and neutral actions are always
allowed (the paper's Def. 3.1 and 4.1, and p. 3: "Actions in Act-up are always
permitted"). An agent that models the contract is checked like any other.

The pre-image, the set of states from which the coalition can force the next
state into a given set, uses only these moves (the paper's Def. 4.2-4.3 and
Algorithm 1). So agent 1 with 5 in the wallet cannot win through a `D20` move.
If, at some state, every transition needs an action that some agent cannot pay
for at that state, model checking stops with an error naming the state: a game
structure gives each agent at least one move per state (JACM 2002 Def. 2.1).

Balances come from the `Wallets` section, one row per state. A wallet guard
(`wallet(agent, op, value)`, see [Formula language](#formula-language)) keeps the
states whose balance meets it; balances are not recomputed along transitions.

Implementation techniques (transition cache, early-stop): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Coalition syntax | Wallet-aware | Dedicated `<<...>>` (avoids clash with `<A><k>`) |
| Wallet dynamics | Balances change along transitions (Def. 4.4) | Balances read from `Wallets`; moves checked against them; not updated along transitions |
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
