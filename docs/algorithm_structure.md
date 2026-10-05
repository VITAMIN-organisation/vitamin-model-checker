# Algorithm Structure Guide

How algorithm docs are organized in VITAMIN, and how the explicit checkers
share one runtime shape.

Related pages:

- [logic_knowledge_base.md](logic_knowledge_base.md): cross-logic syntax map
- [file_formats.md](file_formats.md): model file layout
- [algorithm_design.md](algorithm_design.md): shared caches, data structures,
  cleanup, and performance techniques
- `docs/<Logic>/algorithm.md`: denotations and code path for one logic

## Section Order For `algorithm.md`

```text
1. Scope
2. Model
3. Formula language
4. Semantic denotations
5. Theory vs implementation
6. Model-checking pipeline
7. Code map
8. Tests
```

Keep algorithm pages focused on what the checker computes. Put shared
implementation techniques (caches, bit vectors, zone graphs, cache reset) in
[algorithm_design.md](algorithm_design.md), not as long repeated blocks in each
logic page. A one-line pointer from a logic page is enough when that logic uses
a listed technique.

## Runtime Shape

```text
formula text
  -> formula parser
  -> AST / formula tree
  -> (optional) symbolic structure (zone graph for timed logics)
  -> operator handlers / fixpoints
  -> satisfying set (states or regions)
  -> initial-state check
  -> result dict
```

Package layout used by most logics:

```text
model_checker/algorithms/explicit/<Logic>/
  <Logic>.py      # model_checking entry
  solver.py       # dispatch
  operators.py    # denotations
  preimage.py     # Pre / obstruction / coalition step (if needed)
  util/           # validation helpers (if needed)
```

## Logic Families

| Family | Logics | Model type | Core pattern |
|---|---|---|---|
| Classical branching | `CTL`, `ATL`, `ATLF` | `CGS` | Pre-image + fixpoints |
| Automata-theoretic | `ATL_STAR` | `CGS` | LTL to deterministic parity automaton, producted with the CGS, solved as a 2-player game (not pre-image/fixpoints) |
| Strategy-bounded | `NatATL`, `NatATLF`, `NatSL` | `CGS` | Strategy search / pruning |
| Cost / resource / wallet | `OATL`, `COTL`, `RBATL`, `RABATL`, `CapATL`, `Wallet_ATL` | `costCGS` / `capCGS` / `WalletCGS` | Bound-aware coalition operators |
| Intuitionistic | `ICTL`, `IATL` | `BirelationalMatrix` / `BCGS` | Upward closure + dual Pre |
| Timed | `TCTL`, `TOL` | `timedCGS` | Zone graph + regional / obstruction solve |
| Linear cost | `OL` | `costCGS` | Demonic cost prefix on paths |

## Reading Path

1. Pick a logic in [logic_knowledge_base.md](logic_knowledge_base.md).
2. Open `docs/<Logic>/algorithm.md` for denotations and code path.
3. Open [algorithm_design.md](algorithm_design.md) for shared caches and
   techniques used by that logic.
4. Use [file_formats.md](file_formats.md) when editing models.
