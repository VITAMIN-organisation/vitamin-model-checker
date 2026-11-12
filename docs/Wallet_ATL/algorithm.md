# Wallet_ATL algorithm reference

This page gives the denotations and code path of Wallet_ATL in
`model_checker/algorithms/explicit/Wallet_ATL/`, for developers reading or
changing the checker; the syntax is in the
[knowledge base](../logic_knowledge_base.md#wallet_atl), the model format in
[WalletCGS sections](../file_formats.md#walletcgs-sections) and modeling
examples in [usage.md](usage.md).

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
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)), and
`<<A>>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

The `<<...>>` prefix is mandatory before temporal operators. Empty `<<>>` is
invalid.

A guard is written `wallet(agent, op value)`, with `op` one of `>=`, `<=`, `==`,
`>`, `<`, and guards are joined with `&&`, as in
`<<1,2:wallet(1, >= 10) && wallet(2, >= 0)>>`. Every guard of a formula must
hold, and a coalition agent with no guard is unconstrained.

Two rules go beyond the Wallet ATL paper (AAMAS 2026, cited under
[Semantic denotations](#semantic-denotations)):

- Each guard names an agent of the coalition. The paper's grammar lets a guard
  name any agent, but its Def. 4.5 and Algorithm 1 write the guards over the
  coalition agents only. The checker accepts the narrower form, so a guard on
  another agent (`<<1:wallet(2, >= 5)>>`) is a syntax error that names the
  agent.
- An agent may have several guards, as in the range
  `wallet(1, >= 3) && wallet(1, <= 5)`. The paper gives each agent one bound;
  the meaning of several guards follows from its truth definition of one guard
  (`wallet(a, op v)` holds at a state when the balance of `a` there meets
  `op v`) and from `&&`.

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

Balances come from the `Wallets` section, one row per state, and are not
recomputed along transitions. A state with no row is a load error that names
it, because the paper's wallet function assigns "each agent a non-negative
balance in every state" (Def. 3.1, p. 3). A wallet guard
(`wallet(agent, op value)`, see [Formula language](#formula-language)) is
checked at the state where a coalition move starts; [Operators](#operators)
says where each operator checks it.

### Operators

In a formula `<<A:C>>...`, `A` is the coalition and `C` is the conjunction of
its wallet guards (none for a plain `<<A>>`). `Pre(A, S)` is the pre-image
above, `wPre(S)` keeps the states of `S` where every guard in `C` holds (all of
`S` when `C` is empty; the paper's Algorithm 2), and `[[phi]]` is the set of
states where the operand `phi` holds; `psi` is the goal of U and F. A fixpoint
is computed by repeating one step until the set stops changing, and `rho` is the
set built so far. Table 1 lists how each operator is computed:

**Table 1: Wallet_ATL operators and the lines of the paper's Algorithm 1 they follow.**

| Formula | Computed as | Paper |
| :--- | :--- | :--- |
| `<<A:C>>X phi` | `wPre(Pre(A, [[phi]]))` | Algorithm 1 line 9 |
| `<<A:C>>G phi` | from all states, repeat: `rho` becomes the states of `wPre(Pre(A, rho))` that are in `[[phi]]` | Algorithm 1 lines 10-17 |
| `<<A:C>>phi U psi` | from `[[psi]]`, repeat: add to `rho` the states of `wPre(Pre(A, rho))` that are in `[[phi]]` | Algorithm 1 lines 18-25 |
| `<<A:C>>F psi` | equals `<<A:C>>true U psi` | not in the paper's grammar, which has X, U and G |

For example, take s0 with 10 in agent 1's wallet, whose only move leads to s1
with 5, where `goal` holds. With `C = wallet(1, >= 10)`, `<<1:C>>X goal` holds
at s0: the guard holds where the move starts, and the next state need not meet
it. `<<1:C>>F goal` holds at s0 and at s1.

### Open questions

The paper is silent on these cases or gives two answers. The code keeps the
answer named in each item:

- The start set of U and F: the paper's Algorithm 1 line 20 starts from
  `[[psi]]` with no guard, so a state where `psi` already holds counts even if
  the guard fails there (s1 in the example). The paper's prose says "provided
  all wallet constraints are satisfied". The code follows Algorithm 1, which also
  keeps `<<A:C>>X psi` implying `<<A:C>>F psi`.
- Where the guard is checked: Algorithm 1 checks it in every round of G and U,
  so at every state of the path, while the paper's Def. 4.5 checks it only at the
  first state of a path. The code follows Algorithm 1.
- A state where the guard fails, for X, for G, and for U where `psi` does not
  hold: Def. 4.5 keeps only the paths whose first state meets every guard of `C`,
  so read literally it makes the formula true there by vacuity (a claim about
  all of zero paths). Algorithm 1 and the prose make it false, and so does the
  code.
- G when `phi` holds at every state: Algorithm 1's starting set already equals
  its first update, so it skips the loop and returns all states, guard or not.
  The code applies `wPre` in every round, as in the other cases.
- Balance updates: the paper's Def. 4.4 changes only the acting agent's wallet,
  while its section 3.2 and Example 3.3 also move the amount to or from the
  contract. The code applies neither rule (see
  [Semantic denotations](#semantic-denotations)).
- A consumption letter with no amount (`D`): the paper's Def. 3.1 takes amounts
  `v` in the positive integers; the code treats `D` as a neutral action.

Implementation techniques (transition cache, early-stop): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

Table 2 sets the paper next to what the code does:

**Table 2: Wallet_ATL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Coalition syntax | Wallet-aware | Dedicated `<<...>>` (avoids clash with `<A><k>`) |
| Wallet dynamics | Balances change along transitions (Def. 4.4) | Balances read from `Wallets`; moves checked against them; not updated along transitions |
| Temporal ops | X, U, G | X, U, G, and F as `true U` (see [Operators](#operators)) |
| Wallet predicate as a formula | `wallet(a, op v)` is a state formula of the paper's grammar, for any agent | Not supported: `wallet(...)` is accepted only as a guard inside `<<A:...>>`, and is a syntax error elsewhere |

## Model-checking pipeline

```text
WalletCGS.read_file -> Wallet_ATLParser.parse -> _convert_wallet_ast
  -> build_resolved_formula_tree -> build_feasible_transition_cache
  -> solve_tree -> result
```

Entry: `Wallet_ATL/Wallet_ATL.py`.

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
