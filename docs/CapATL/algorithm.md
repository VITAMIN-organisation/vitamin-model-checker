# CapATL algorithm reference

This page covers the denotations and code path of the CapATL checker in
`model_checker/algorithms/explicit/CapATL/`, for a developer reading or changing
it; the logic is described in the
[knowledge base](../logic_knowledge_base.md#capatl) and the model file format in
[capCGS sections](../file_formats.md#capcgs-sections).

## Model

- Type: `capCGS`
- Capacities constrain available actions via model sections, not a numeric
  formula bound `k`.

## Formula language

Parser: `parsers/formulas/CapATL/parser.py`

```text
phi ::= ... | <{A}> X phi | <{A}> F phi | <{A}> G phi | <{A}> phi U psi
           | <{A}> (phi U psi) | <{A}> phi R psi | <{A}> (phi R psi)
           | Ka(cap)                         -- a = agent number
cap ::= a is c | !cap | cap && cap | cap || cap | cap -> cap
      | true | false | (cap)             -- c = capacity name
```

`Ka(cap)` is the knowledge operator K^a_cap(phi) of AAMAS 2024:
"agent a knows that the capacity assignment verifies phi". A
capacity assignment gives each agent one of its capacities (the model's
`Capacities_assignment` rows list which ones it may take). `cap`, the paper's
capacity assignment formula, is written with `a is c` for the paper's `a -> c`:
`a` is an agent number and `c` a capacity name from the model's `Capacities`
section. For example, `K2(!(3 is c) && 1 is cop)` says that agent 2 knows that
agent 3 does not have capacity `c` and agent 1 has `cop`.

- Forms: `K1(...)`, with `kcap1(...)` as the word alias, like `until` for `U`.
  It may stand alone (`K1(1 is c)`) or inside any formula
  (`<{1}> F (g && K1(1 is c))`). `a is c` is valid only inside it.
- Errors: the parentheses are part of the paper's rule, and the paper's `cap` has
  only `a -> c`, negation and conjunction (the paper adds disjunction, implication,
  true and false as sugar). So `K1 1 is c`, `K1(K2(1 is c))` and `K1(p)` are
  errors with a message that names the part, and so is an agent out of range.
- Names: `K1x` and `K12x` are each read as one word, not as the operator `K1`
  followed by `x`, and refused as names because they start with a capital
  ("Atomic proposition 'K1x' is invalid: ..."). The bare word `kcap` is reserved
  in CapATL (see
  [names and keywords](../logic_knowledge_base.md#names-and-keywords)).
- Precedence: the paper states none inside `cap`; the parser uses the one of the
  other connectives (`!`, then `&&`, then `||`, then `->`).

`<{A}> phi U psi` and `<{A}> (phi U psi)` build the same tree, and so do the two
forms of `R` (see
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)).
`<{A}>F p && q` is a syntax error that asks for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

Formula bound `<{A}, k>` is rejected (no numeric `k` in CapATL). `W` is
unsupported.

## Semantic denotations

Coalition modalities over capacity-restricted transitions. Release uses a
greatest fixpoint in the CapATL solver. The solver has no semantics for the
knowledge operator: model checking a formula that contains `Ka(...)` anywhere
returns an error of type `validation` with the message "The knowledge operator
K1(...) is parsed but not evaluated by the CapATL solver yet", instead of a
result.

Implementation techniques (lru caches + clear, state index cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

Table 1 sets the theory beside this implementation.

**Table 1: CapATL theory and implementation.**

| Aspect | Theory | Implementation |
| :--- | :--- | :--- |
| Coalition | `<{A}>` | Braces required; no formula `k` |
| `Ka(cap)` | Knowledge over capacity assignments | Parsed; model checking returns an error |
| Capacities | Model constraints | `capCGS` sections + Pre over capacity knowledge |

## Model-checking pipeline

```text
capCGS.read_file -> CapATLParser.parse -> build_tree -> solve_tree -> result
```

Entry: `CapATL/CapATL.py`.

## Code map

Table 2 lists the files of the checker and their role.

**Table 2: CapATL code map.**

| Path | Role |
| :--- | :--- |
| `CapATL/CapATL.py` | Entry |
| `CapATL/solver.py` | Dispatch |
| `CapATL/operators.py` | Operators |
| `CapATL/preimage.py` | Pre-image |
| `CapATL/knowledge.py` | Knowledge helpers |

## Tests

CapATL fixtures under capCGS / algorithm tests.
