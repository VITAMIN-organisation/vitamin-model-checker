# OL algorithm reference

This page gives the denotations and code path of OL in
`model_checker/algorithms/explicit/OL/`, for developers reading or changing the
checker; the syntax is in the [knowledge base](../logic_knowledge_base.md#ol) and
the model format in [costCGS sections](../file_formats.md#costcgs-sections). The method follows D. Catta, J. Leneutre,
V. Malvone, "Obstruction Logic: a Strategic Temporal Logic to Reason about
Dynamic Game Models", ECAI 2023. OL is the special case
of [OATL](../OATL/algorithm.md) in which no agent makes a choice of its own, so
OL keeps only its parser and entry point and runs the OATL solver (see
[Semantic denotations](#semantic-denotations)).

## Model

Type `costCGS` ([format](../file_formats.md#costcgs-sections)), written in one of
two forms:

- `Transition` with `Costs_for_actions`: each cell lists
  [joint actions](../OATL/algorithm.md#idea) (one action per agent), and each joint
  action has a cost at its state. Two joint actions in one cell are two ways to
  reach the same state. Disabling that edge disables both, so it costs the sum of
  their costs.
- `Transition_With_Costs`: each cell is one edge and its cost, as in the paper's
  models (Definition 2). Cell `2` is an edge of cost 2.

In both forms a cost with one entry per agent, such as `1:0`, is summed into one
cost (`1:0` costs 1), as OATL does.

## Formula language

Parser: `parsers/formulas/OL/parser.py`

```text
phi ::= ... | <Jk> X phi | <Jk> F phi | <Jk> G phi
           | <Jk>(phi U psi) | <Jk>(phi R psi) | <Jk>(phi W psi)
```

Prefix must include `J` (`<J5>`). The bound `k` is any natural number, 0 included,
written without a leading zero (`<J01>` is an error): the paper says "n is any
number in N0" (Definition 1). With `k = 0` the Demon can disable nothing, so
`<J0> F goal` holds where every path reaches `goal`.

Table 1 lists the written forms of `U`, `R` and `W` after the prefix (`U` shown):

**Table 1: Accepted forms of `U` after the `<Jk>` prefix.**

| Form | Accepted | Where it comes from |
| :--- | :--- | :--- |
| `<J2> (p U q)` | yes | ECAI 2023, Definition 1: $\langle n\rangle(\varphi\ U\ \varphi)$ and $\langle n\rangle(\varphi\ R\ \varphi)$. |
| `<J2> p U q` | yes | The paper's prose writes this form too, $\langle n\rangle\varphi\ U\ \psi$. |

`W` is the paper's abbreviation
$\langle n\rangle(\varphi\ W\ \psi) := \langle n\rangle(\psi\ R\ (\varphi \lor \psi))$
and takes both forms. Both forms build the same tree (see
[the knowledge base](../logic_knowledge_base.md#until-after-a-prefix)).
`<J2> p && q U r` is `<J2> ((p && q) U r)`, its only reading, because `<J2> p`
alone is no formula. The paper states no
precedence rule, so `<J2> p U q && r` and `<J2>F p && q` are syntax errors that
ask for parentheses (see
[the knowledge base](../logic_knowledge_base.md#prefix-before-a-connective)).

## Semantic denotations

OL is a game of two players on the model's graph: a Traveler moves along the
edges, and a Demon, before each move, may disable some edges leaving the
Traveler's state. The disabled edges cost at most `k` in total and are never all
of that state's edges (Definition 3), so a state with one edge always keeps it.
`<Jk> phi` (with `phi` a temporal formula such as `F goal`) holds at a state when
the Demon has such a strategy under which every path the Traveler can still take
satisfies `phi` (Definition 4). Each step has its own budget of `k`; costs are not
added up over the path.

The checker computes the fixpoints of Theorem 1, where $[\![\varphi]\!]$ is the set
of states where $\varphi$ holds and $Y$ is the set the iteration has reached so far.
$\blacktriangledown(k, Y)$ is the set of states that have an edge into $Y$ and can
disable all their edges to states outside $Y$ for a total cost of at most $k$
(the definition before Proposition 1). Table 2 lists the fixpoints:

**Table 2: The OL operators as fixpoints (ECAI 2023, Proposition 1 and Theorem 1).**

| Formula | Set of states |
| :--- | :--- |
| `<Jk> X phi` | $\blacktriangledown(k, [\![\varphi]\!])$ |
| `<Jk>(phi U psi)` | least fixpoint of $[\![\psi]\!] \cup ([\![\varphi]\!] \cap \blacktriangledown(k, Y))$ |
| `<Jk>(phi R psi)` | greatest fixpoint of $[\![\psi]\!] \cap ([\![\varphi]\!] \cup \blacktriangledown(k, Y))$ |

`F phi` is `true U phi`, `G phi` is `false R phi` and `phi W psi` is
`psi R (phi || psi)`, the abbreviations of the paper.

OATL has the same Demon, but there a coalition of agents also picks its part of
each joint action. With the coalition of all agents, the agents pick the whole
joint action, which is the Traveler's single move in OL. The OATL
paper (AAMAS 2024, see [OATL](../OATL/algorithm.md)) states this for a formula without nested
strategic operators: $\mathfrak{M}, s \models_{OL} \langle\langle n\rangle\rangle\psi$
iff $\mathfrak{M}, s \models [\![Ag]\!]^n\psi$, where $[\![Ag]\!]^n$ is the OATL
operator for the coalition $Ag$ of all agents with budget $n$. The paper adds
that this "can be extended in the obvious way for boolean and temporal
operators". So `OL/solver.py` reads `<Jk>` as that coalition with budget `k` and
runs the OATL operators.

A joint action with no cost in the model cannot be disabled. If a result would
change were it disabled, the check fails with an error of type `model` that names
the states and actions, as in [OATL](../OATL/algorithm.md#model).

## Model-checking pipeline

```text
costCGS.read_file -> OLParser.parse -> build_resolved_formula_tree -> solve_tree -> result
```

Entry: `OL/OL.py`.

## Code map

Table 3 lists the files OL runs; paths are relative to
`model_checker/algorithms/explicit/`.

**Table 3: OL code map.**

| Path | Role |
| :--- | :--- |
| `OL/OL.py` | Entry |
| `OL/solver.py` | Entry to the OATL solver with the coalition of all agents |
| `OATL/solver.py`, `OATL/operators.py`, `OATL/preimage.py` | Operators and Demon pre-image shared with OATL |

## Tests

`model_checker/tests/integration/algorithms/ol/test_correctness.py` checks state
sets worked out by hand from Table 2 on the fixtures in
`model_checker/tests/fixtures/costCGS/OL/`. In `ol_demon_1agent_4states.txt` the
Demon's budget decides the result; in `ol_edge_costs_2agents_3states.txt` the
costs come from `Transition_With_Costs`.
