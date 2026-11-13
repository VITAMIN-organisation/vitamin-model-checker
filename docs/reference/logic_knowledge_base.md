# Logic knowledge base

This is the cross-logic theory and syntax map for VITAMIN, for a developer who
writes formulas in several logics or adds a logic. The per-logic pages in
[docs/algorithms/](../algorithms/index.md) (for example
[ictl.md](../algorithms/ictl.md)) say how each checker computes its operators and
which model checks it runs, and
[file_formats.md](file_formats.md) says how to author `.txt` models.

After the syntax every logic shares, the page has one section each for CTL,
ATL*, NatSL, OATL, OL, RBATL and RABATL, CapATL, COTL, Wallet_ATL, ICTL, IATL, TCTL
and TOL. LTL, ATL, ATLF, NatATL (with NatATL_Recall) and NatATLF have no section
here: their syntax is in the [syntax cards](#syntax-cards) and the rest on their
pages, listed in [algorithm design](../algorithms/index.md).

## Contents

- [Boolean logic (shared syntax)](#boolean-logic-shared-syntax)
- [CTL (Computation Tree Logic)](#ctl---computation-tree-logic)
- [ATL*](#atl-star)
- [NatSL](#natsl---natural-strategy-logic)
- [OATL](#oatl)
- [OL](#ol)
- [RBATL / RABATL](#rbatl--rabatl)
- [CapATL](#capatl)
- [COTL](#cotl)
- [Wallet_ATL](#wallet_atl)
- [ICTL](#ictl---intuitionistic-ctl)
- [IATL](#iatl---intuitionistic-atl)
- [TCTL](#tctl---timed-ctl)
- [TOL](#tol---timed-obstruction-logic)
- [Empty and repeated coalition policy](#empty-coalition-policy)
- [Names and keywords](#names-and-keywords)
- [Syntax cards](#syntax-cards)
- [Logic comparison matrix](#summary-logic-comparison-matrix)
- [Model syntax](#model-syntax)

<a id="boolean-logic-shared-syntax"></a>
## Boolean logic (shared syntax)

All logics in VITAMIN share a common set of boolean operators and constants. The
boolean constants are `true` and `false`. Table 1 lists the boolean operators,
ordered by precedence:

**Table 1: Boolean operators, ordered by precedence.**

| Operator | Syntax | Description |
| :--- | :--- | :--- |
| Negation | `!` | Logical NOT |
| Conjunction | `&&` | Logical AND |
| Disjunction | `\|\|` | Logical OR |
| Implication | `->` | Logical implication (p -> q) |

The word forms `not`, `and`, `or` and `implies`, and the logics that read them, are
in [word operators](#word-operators).

Every logic spells the connectives this way. A single `&` or `|`, and `>` as
implication, are rejected in all of them
(`model_checker/tests/unit/parsers/formulas/test_connective_spelling.py`), so a
connective spelling is accepted by every logic except NatSL, or by none. NatSL
goals take no connectives.

### Grouping and nesting

Table 2 lists the brackets that group a formula and the logics that take them:

**Table 2: Grouping and nesting brackets.**

| Syntax | Description | Supported logics |
| :--- | :--- | :--- |
| `(...)` | Standard grouping | All logics |
| `[...]` | Around the Until of a path quantifier, `A[p U q]` (CTL, ICTL), or its Release, `E[p R q]` (ICTL) | CTL and ICTL only |

CTL writes square brackets only around an Until, `A[f1 U f2]`, and groups
everything else with parentheses (Clarke, Emerson, Sistla, ACM TOPLAS 1986).
ICTL writes them once, around a Release (EUMAS25b, Bozzelli et al., EUMAS 2025), and ICTL
also takes them around an Until because its grammar treats U and R alike (see
[the ICTL reference](../algorithms/ictl.md)). `[p] && q` and `AF [p]` are syntax
errors, and so is `[...]` as grouping in every other logic (IATL writes `[1,2]` as a
coalition, see [IATL](#iatl---intuitionistic-atl)).

### Until after a prefix

A prefix is the part of a formula that scopes over what follows it: a coalition
(`<1>`, `<<1>>`), a coalition with a bound or budget (`<1><5>`, the OL and TOL
Demon budgets `<J5>` and `{J2}`) or a CTL path quantifier (`A`), each with the temporal
operator after it (`<1>F`, `AF`), and the TCTL/TOL freeze `j.`. In every logic
with a prefix before Until, `prefix p U q` and `prefix (p U q)` are the same
formula and build the same tree: `<1> p U q` and `<1> (p U q)`, `<J5> p U q` and
`<J5> (p U q)`, `A p U q` and `A(p U q)`. ATL writes the first form (Alur,
Henzinger, Kupferman, JACM 2002), and the obstruction logics write the
second. ATL* reads `<<A>> p U q` the same way; the other ATL* forms
are in [ATL*](#atl-star). Release (`R`) and Weak Until
(`W`) follow the same rule where a logic has them. The 17 logics covered are listed
in `model_checker/tests/unit/parsers/formulas/test_until_after_prefix.py`.

### Prefix before a connective

When no parenthesis closes a prefix, a connective after it has two readings:
`<1>F p && q` is `(<1>F p) && q` or `<1>F (p && q)`, and `<1> p U q && r` is
`(<1> (p U q)) && r` or `<1> (p U (q && r))`. No defining paper states which, so in
every logic with a prefix this is a syntax error that gives the position and both
readings, for `&&`, `||` and `->` in any spelling (`and`, `or`, `implies`):

```text
'<1>F ... && ...' is ambiguous: write <1>F (... && ...) for <1>F over both sides,
or (<1>F ...) && ... for <1>F over the left side only (position 0)
```

The same holds after a negation (`!<1>F p && q`), after a connective
(`q && <1>F p && r`) and after a TCTL/TOL clock constraint (`AF p : x<5 && q`).
These parse, because they have one reading:

- A prefix at the end: `q && <1>F p`.
- A prefix closed by parentheses: `(<1>F p) && q`, `<1>F (p && q)`,
  `<1> (p U q) && r`.
- A connective in the left operand of a prefix Until: `<1> p && q U r` is
  `<1> ((p && q) U r)`, because `<1> p` alone is no formula of these logics.

ATL* differs, because `<<1>> p` and a bare Until inside a coalition are ATL*
formulas; its rules and messages are in [ATL*](#atl-star).
LTL has no prefix: its `F`, `G`, `X` and `U` follow the precedence table of the
[Spot LTL library](https://spot.lre.epita.fr/tl.pdf), so
`F p && q` is `(F p) && q`, `p U q && r` is `(p U q) && r` and `F p U q` is
`(F p) U q`. One rule differs: Spot ranks `!` above `U` (Spot-tl, Sec. 3.1, p. 15), while
VITAMIN reads `!p U q` as `!(p U q)`. Write `(!p) U q` for Spot's reading.
NatSL has no connectives after its prefix, so it rejects `E{1}x: (x, 1) F p && q`
without offering two readings; see [NatSL](#natsl---natural-strategy-logic).

### Operators and names

Temporal operators (`X`, `F`, `G`, `U`, in CTL and ICTL `AX`, `AF`, `AG`, `EX`, `EF`, `EG`, and in TCTL `AF`, `AG`, `EF`, `EG`) are words of their own. TCTL has no `X` (see [the TCTL reference](../algorithms/tctl.md)).
Follow one with a space, `(` or `!`: `F p`, `F (p && q)`, `F !p`.

A name starts with a lowercase letter ([names and keywords](#names-and-keywords)), so an operator glued to a name, such as `Fp`, is an error; the three ways it fails are in [operators glued to a name](#operators-glued-to-a-name).
A binary operator follows the same rule: `pUq` starts lowercase, so it is one name like any other and must be declared in the model; `p U q` is the Until.

Every logic follows this rule, and `model_checker/tests/unit/parsers/formulas/test_operator_spacing.py` checks it for each registered logic.

A name the model does not declare is an error in every logic, wherever it sits in the formula: under `!`, inside an Until or a conjunction.
The error type is `semantic` (NatSL reports `validation`), so a typo never reads as a proposition that is false everywhere, which would make `AG !typo` true.
The message names it: "Proposition(s) 'zz' not among the model's declared propositions [...]". Two logics word it differently: ATL* gives "'zz' is not among the model's declared propositions [...]" and NatSL "Unknown proposition 'zz'; model propositions are [...]".
`model_checker/tests/integration/algorithms/test_error_contract.py` checks this for each registered logic.

The truth table of the boolean operators:

```text
   p   |   q   |  !p   | p && q | p || q | p -> q
-------|-------|-------|--------|--------|--------
 true  | true  | false |  true  |  true  |  true
 true  | false | false |  false |  true  |  false
 false | true  | true  |  false |  true  |  true
 false | false | true  |  false |  false |  true
```

<a id="ctl---computation-tree-logic"></a>
## CTL (Computation Tree Logic)

### Theoretical background

CTL is a branching-time logic defined over computation trees. Formulas are evaluated at a state and quantify over all possible infinite paths from that state.

#### Standard syntax

- Path quantifiers:
    - `E`: there exists a path...
    - `A`: for all paths...
- Temporal operators:
    - `X`: next state
    - `F`: eventually (finally)
    - `G`: globally (always)
    - `U`: until

#### Standard examples

- `AG p`: always globally p (p is an invariant).
- `EF p`: eventually p (reachability).
- `AG (p -> AF q)`: always if p, then eventually q on all paths (liveness/response).

### Syntax

The checker accepts:

- Path quantifiers `E` / `A` with temporal operators `X`, `F`, `G`, and `U`.
- Boolean connectives shared with the common formula syntax.

The model type is `CGS`. How the checker computes each operator:
[CTL algorithm](../algorithms/ctl.md); the witness or counterexample path it can
return: [traces](../algorithms/ctl.md#traces).

<a id="atl-star"></a>
## ATL*

ATL* lets a coalition scope over any path formula, including nested coalitions,
on a `CGS` model. A state formula `phi` holds at a state; a path formula `psi`,
such as a bare Until, holds on a path:

```text
phi ::= p | !phi | phi && phi | phi || phi | phi -> phi | <<A>> psi
psi ::= phi | !psi | psi && psi | X psi | psi U psi | F psi | G psi | <<A>> psi
```

A temporal operator outside a coalition parses but is an error when checked:
`p && X q` gives "a bare Next is not a state formula; temporal operators need a
<<...>> coalition around them".

A coalition is written `<<1,2>>`, with agent ids in `1..n`; an empty coalition is
a syntax error. ATL writes a coalition with single angle brackets (`<1,2>`);
Wallet_ATL uses `<<...>>` with a different meaning ([Wallet_ATL](#wallet_atl)).

Table 3 lists the written forms of an Until under a coalition:

**Table 3: Until under an ATL* coalition.**

| Form | Reading |
| :--- | :--- |
| `<<A>> x U y` | The coalition covers the Until: the same tree as `<<A>> (x U y)` |
| `<<A>> (x U y)` | The coalition covers the Until |
| `(<<A>> x) U y` | The coalition covers only the left operand; this is a path formula, so it is checkable only inside another coalition, as in `<<B>> ((<<A>> x) U y)` |

Each operand of that `U` is one unary formula, so `<<1>> X p U q` is
`<<1>> ((X p) U q)` and `X <<1>> p U q` is `X (<<1>> (p U q))`.

`!`, `X`, `F` and `G` bind tighter than the connectives: `<<1>> (F p && G q)` is
`<<1>> ((F p) && (G q))`. These are syntax errors that ask for parentheses:

- A second `U`, as in `<<1>> p U q U r` or `p U q U r`.
- `U` next to `&&`, `||` or `->`, as in `p U q && r` or `p && q U r`. The messages
  are `'x U y && z' is ambiguous: write (x U y) && z or x U (y && z)` and
  `'x && y U z' is ambiguous: write (x && y) U z or x && (y U z)`, with the
  position of the `U`.
- A connective right after a coalition, as in `<<1>> p && q`, `<<1>> F p && q` or
  `<<1>> (p U q) && r`: in ATL* `<<1>> p && q` can be `(<<1>> p) && q` or
  `<<1>> (p && q)`. Write `(<<1>> F p) && q` or `<<1>> (F p && q)`. A coalition at
  the end, `q && <<1>> F p`, has one reading.

An atom the model does not declare is an error: "'zz' is not among the model's
declared propositions ['p', 'q']". How the checker works:
[ATL* algorithm](../algorithms/atl_star.md).

<a id="natsl---natural-strategy-logic"></a>
## NatSL (Natural Strategy Logic)

### Theoretical background

NatSL quantifies over bounded natural strategies and binds those strategies to
agents. The checker implements a restricted one-goal fragment.

#### Standard syntax

- Existential / universal strategy quantifiers with complexity bounds: `E{k}x`,
  `A{k}y`.
- Explicit agent bindings: `(x, 1)(y, 2)`.
- Temporal goals: `F`, `G`, `X`, and their negations.

A representative formula is:

```text
E{2}controller A{1}opponent: (controller, 1)(opponent, 2) F goal
```

### Syntax

The checker accepts:

- Ordered prefixes of the form `E* A*`, including purely existential prefixes. The
  parser also accepts other orders (`A{1}x E{1}y:`); model checking then returns
  a validation error that asks for an `E* A*` prefix.
- Multi-character strategy variables and explicit agent bindings. The bindings cover
  every agent of the model exactly once, so `E{1}x: (x, 1) F goal` checks only on a
  1-agent model.
- A goal is `F`, `G` or `X` (uppercase), a space and one proposition (`F goal`),
  or its negation, written before the operator (`!F goal`, `not F goal`; `F !goal`
  is rejected); see
  [operators and names](#operators-and-names). A connective in a goal, as in
  `E{1}x: (x, 1) F p && q` or `F (p && q)`, is rejected with "Unsupported goal;
  this prototype accepts F p, G p, X p and their negations, with an uppercase
  operator and a space after it".
- Each strategy variable is quantified once and bound once, each agent is bound
  once, and each bound `{k}` is at least 1.

The model type is `CGS`. How the strategies are searched and the `space` and `time` modes:
[NatSL algorithm](../algorithms/natsl.md).

<a id="oatl"></a>
## OATL

### Theoretical background

OATL (Obstruction Alternating-time Temporal Logic) is defined in D. Catta,
J. Leneutre, V. Malvone, A. Murano, "Obstruction Alternating-time Temporal
Logic: a Strategic Logic to Reason about Dynamic Models", AAMAS 2024. Besides
the agents of a [`costCGS`](file_formats.md#costcgs-sections), a single extra
player, the Demon, can temporarily erase transitions. Erasing joint action `a` at
state `s` costs `$(s, a)`.

#### Standard syntax

- Coalition with a budget: `[[A]]_n theta` in the paper, `<A><n> theta` in VITAMIN
    - `A`: the coalition of agents.
    - `n`: the Demon's budget per step.
- Operators: the paper's grammar has `X`, `U` and `R` only (Def. 1). VITAMIN also
  reads `F`, `G` and `W`, which OL defines as abbreviations (ECAI 2023, after
  Def. 1): `F phi` is `true U phi`, `G phi` is `false R phi`, and `phi W psi` is
  `psi R (phi || psi)`.

#### Semantics

- `<A><n> theta` holds at `s` when the Demon has a strategy that, at each step,
  erases a set of joint actions of total cost at most `n` (never all of them),
  such that for every strategy of `A`, some remaining path satisfies `theta`.
  The agents outside `A` resolve the remaining choices in the Demon's favour.
- The budget applies to each step separately; it is not a sum along the path.
- Example: on the model of the paper's Figure 1
  (`model_checker/tests/fixtures/costCGS/OATL/oatl_3agents_medium_6states_costs.txt`),
  `<1,2><2> G !(r && s && g)` is false at `s0` and `<1,2><3> G !(r && s && g)`
  is true. The least budget that stops the attack is 3, as the paper states.

### Syntax

#### Supported syntax

- Format: `<coalition><budget>` (e.g., `<1,2><10>`), with no space between
  the two parts (`<1> <5>` is an error).
- Temporal operators: `X`, `F`, `G`, `U`, `R`, `W` (and their keywords).
- Propositions: `[a-z][a-zA-Z0-9_]*` (see [names and keywords](#names-and-keywords)).
- Boolean constants: `true` and `false`.

#### Validation rules

- Budget requirement: a budget is mandatory for every coalition-prefixed temporal operator.
- Budget value: the budget `n` is an integer `n >= 0` with no leading zeros. With `n = 0` the Demon can erase only zero-cost joint actions.
- Parentheses: binary operators may be written as in the paper, `<A><n> (phi U psi)`, or without parentheses.

#### Formula examples

```text
<1><5> F goal
<1,2><10> (safe W unsafe)
<1,2><3> (false R !(r && s && g))
<1><0> X p
```

How the checker computes each operator and reads costs and missing costs:
[OATL algorithm](../algorithms/oatl.md).

<a id="ol"></a>
## OL

### Theoretical background

OL (Obstruction Logic, ECAI 2023) is a game against a Demon on `costCGS` models: `<Jk> phi` holds when the Demon, with a budget of `k` at each step, can disable edges so that every remaining path satisfies `phi`.
It is OATL with the coalition of all agents.
How the checker computes it: [OL algorithm](../algorithms/ol.md).

The paper writes `<n> X phi`, `<n> (phi U psi)` and `<n> (phi R psi)`, where `n` is a natural number, 0 included (ECAI 2023, Def. 1); VITAMIN writes the prefix `<Jn>`.

### Syntax

#### Supported syntax

- Format: `<Jk>` (e.g., `<J5>`). The letter `J` is mandatory inside the angle brackets.
- Temporal operators: `X`, `F`, `G`, `U`, `R`, `W`.
- Propositions: `[a-z][a-zA-Z0-9_]*` (see [names and keywords](#names-and-keywords)).

#### Validation rules

- Mandatory `J`: OL prefixes must use `<Jk>`, not bare `<k>`.
- Budget requirement: every temporal operator must be prefixed with `<Jk>`.
- Budget value: `k >= 0` with no leading zero; `<J0>` is valid and `<J01>` is rejected.

#### Formula examples

```text
<J5> F goal
<J10> G ok
<J3> (p U q)
```

How the checker computes each operator: [OL algorithm](../algorithms/ol.md).

<a id="rbatl--rabatl"></a>
## RBATL / RABATL

### Theoretical background

RBATL and RABATL extend ATL with vector cost bounds on coalition strategies over `costCGS` models.

The standard syntax is the vector bounded coalition `<A><b1, b2, ...> phi`:

- `A`: coalition agents.
- `b1, b2, ...`: per-resource bounds.

### Syntax

RBATL and RABATL accept the same formulas.

#### Supported syntax

- Format: `<coalition><bound1,bound2,...>` (e.g., `<1><10,5>`), with no space
  between the two parts (`<1> <5>` is an error).
- Temporal operators: `X`, `F`, `G`, `U` (`R`/`W` rejected at parser).
- Multi-resource bounds: comma-separated inside the second angle-bracket group.

#### Validation rules

- Comma separation: resource vectors use commas, not colons.
- Bound range: each bound value is between 0 and 1,000,000. `<1><1000001>F p` is an error, "Invalid bound value 1000001: must be between 0 and 1000000".
- Bound 0: a bound of 0 for a resource allows only moves of cost 0 in that resource. The PRIMA 2024 algorithm has its own cases for bound 0 (p. 12, lines 13 and 26).
- Leading zeros: a bound value with a leading zero (`<1><05>F p`, `<1><2,05>F p`) is an error, as in OATL: "Bound cannot have leading zeros (e.g., use <1><5>, not <1><05>)".
- Resource count: the length of the bound vector is not checked against the model. Bound `i` limits cost value `i`; cost values beyond the last bound are not limited, and bounds beyond the last cost value are ignored.

#### Formula examples

```text
<1><100,50> F goal
<1,2><10,10,10> G safe
<1><5> (p U q)
<1><0,0> F goal
```

How the checkers compute each operator and the cost of a joint action:
[RBATL algorithm](../algorithms/rbatl.md) and [RABATL algorithm](../algorithms/rabatl.md).

<a id="capatl"></a>
## CapATL

### Theoretical background

CapATL is ATL on [`capCGS`](file_formats.md#capcgs-sections) models, in which each agent acts within one capacity (a named set of actions), chosen from those the model assigns it; it adds a knowledge operator over the capacity assignment. How the checker picks the capacities: [CapATL algorithm](../algorithms/capatl.md).

#### Standard syntax

- Coalition modality: `<{A}> phi` (paper-style agent set; capacities constrain
  available actions via the `capCGS` model, not a formula numeric bound).
- Knowledge: K^a_cap(phi) (AAMAS 2024),
  "agent a knows that the capacity assignment verifies phi", where phi is a
  capacity assignment formula built from `a -> c` (agent `a` has capacity `c`),
  negation and conjunction.

### Syntax

#### Supported syntax

- Coalition: `<{agent1,agent2,...}>` (curly braces required; no `, k`).
- Knowledge: `Ka(cap)`, as in `K1(2 is c)`, with `kcap1(...)` as the word alias.
  `cap` is a capacity formula: `a is c` (agent number `a` has capacity `c`, a name
  from the model's `Capacities` section), combined with `!`, `&&`, `||`, `->`,
  `true`, `false` and parentheses, with the precedence of the other connectives.
  `K2(!(3 is c) && 1 is cop)` says that agent 2 knows that agent 3 does not have
  capacity `c` and agent 1 has `cop`. `Ka(...)` may stand alone or inside any
  formula (`<{1}> F (g && K1(1 is c))`); `a is c` is valid only inside it.
- Knowledge errors: `K1 1 is c` (no parentheses), `K1(K2(1 is c))` (nested `K`),
  `K1(p)` (an atom inside `K`) and an agent out of range are errors whose message
  names the part. `K1x` and `K12x` are each one word, refused as names because they
  start with a capital ("Atomic proposition 'K1x' is invalid: ..."); the bare word
  `kcap` is reserved (see [names and keywords](#names-and-keywords)).
- Temporal operators: `X`, `F`, `G`, `U`, and binary `R` (Release).

#### Validation rules

- Model requirement: can only be verified against `capCGS` models.
- Formula bound: `<{A}, k>` is rejected (no numeric `k` in CapATL).
- Weak Until: `W` is not part of CapATL path syntax and is unsupported.
- Release: `R` is accepted as a binary operator (`<{A}> phi R psi`).
- Knowledge: `K1(...)` parses, but model checking a formula that contains it
  returns an error of type `validation` that names the operator: "The knowledge
  operator K1(...) is parsed but not evaluated by the CapATL solver yet".

#### Formula examples

```text
<{1,2}> F g
<{1}> G a
<{1,2,3}> X a
<{1}> a R g
<{1}> false R g
```

How the checker computes each operator: [CapATL algorithm](../algorithms/capatl.md).

<a id="cotl"></a>
## COTL

### Theoretical background

COTL (Coalition Obstruction Temporal Logic) is defined in D. Catta, J. Leneutre,
V. Malvone, J. Ortiz, "Coalition Obstruction Temporal Logic: A New Obstruction
Logic to Reason About Demon Coalitions", IJCAI 2025. It runs on an
[`ObstructionModel`](file_formats.md#obstructionmodel-sections-cotl): a graph of states, with no agents, whose edges several
demons can temporarily disable. Each demon action has a cost, and the idle
action `*` costs 0. The attacker is the path itself.

#### Standard syntax

- Legion modality: `<<G>>_n theta` in the paper, `<G><n> theta` in VITAMIN
    - `G`: a set of demons (a legion), possibly empty.
    - `n`: the legion's budget per step, `n >= 0`.
- Operators: `X`, weak next (`X~` in the paper, `WX` in VITAMIN), `U`, `R` are primitive; `F`, `G`, `W` are derived.

#### Semantics

`<G><n> theta` holds when the legion has a strategy that, at
each step, picks one action per member of total cost at most `n`, such that
every path left by the disabled edges satisfies `theta`, whatever the other
demons do. A path may stop when every edge out of its last state is disabled.
Example: on the case-study attack graph of the paper
(`model_checker/tests/fixtures/ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt`),
`<1,3><1> G !q` holds at `s0` and `<1,2><1> G !q` does not. Sec. 5 states these
two results for an unspecified budget `n` and gives no cost values, only that the
attacks a10, a20, b12 and b22 cost more than the budget; the budget 1 and the
costs come from the fixture.

COTL and OATL both come from obstruction logic, but they share no checker
code. In OATL a single Demon helps against a coalition of agents on a
`costCGS` (see [OATL](#oatl)). In COTL a legion of demons acts against the
other demons and the path, on an `ObstructionModel`.

### Syntax

#### Supported syntax

- Format: `<legion><budget>` (e.g., `<1,3><1>`, `<><0>`). Demon indices go from 1 to `Number_of_demons`.
- Temporal operators: `X`, `WX` (weak next), `F`, `G`, `U`, `R`, `W`. Binary operators may be written `<G><n> (phi U psi)` or without parentheses.
- Propositions: `[a-z][a-zA-Z0-9_]*` (see [names and keywords](#names-and-keywords)).

#### Formula examples

```text
<1,3><1> G !q
<1><2> WX safe
<><0> X p
<1,2><3> (p U q)
```

How the checker computes each operator, and which operators hold on a path that
stops: [COTL algorithm](../algorithms/cotl.md).

<a id="wallet_atl"></a>
## Wallet_ATL

ATL with wallet-aware coalitions over [`WalletCGS`](file_formats.md#walletcgs-sections) models.

The coalition syntax is `<<agents[:wallet constraints]>>` followed by a temporal formula.
The `<<>>` prefix is mandatory before `X`, `F`, `G`, or `U`; bare temporal operators without a coalition are rejected.
A guard is written `wallet(agent, op value)`, with `op` one of `>=`, `<=`, `==`,
`>`, `<` and `value` a natural number, and guards are joined with `&&` only, as in
`<<1,2:wallet(1, >= 10) && wallet(2, >= 0)>>`. Every guard must hold; a coalition
agent with no guard is unconstrained, and one agent may have several guards
(`wallet(1, >= 3) && wallet(1, <= 5)`). Each guard names a coalition agent:
`<<1:wallet(2, >= 5)>>` is a syntax error that names agent 2. `<<>>` with no agent
is an error.

Wallet_ATL writes `<<...>>` instead of ATL's `<1>` because its guards sit inside
the prefix, after the agents. ATL* also writes `<<...>>`, with a different meaning
([ATL*](#atl-star)).

For example:

```text
<<1>>X auction_active
<<1,2:wallet(1, >= 50)>>G funded
```

The temporal operators are `X`, `F`, `G`, `U`. The model type is `WalletCGS`. See [Wallet_ATL usage](../examples/wallet_atl_usage.md).

Which moves an agent can pay for and where each operator checks the guard:
[Wallet_ATL algorithm](../algorithms/wallet_atl.md) (see its
[payable moves](../algorithms/wallet_atl.md#payable-moves) and
[operators](../algorithms/wallet_atl.md#operators)).

<a id="ictl---intuitionistic-ctl"></a>
## ICTL (Intuitionistic CTL)

### Theoretical background

ICTL (Intuitionistic CTL) extends CTL with intuitionistic propositional
connectives over [birelational models](file_formats.md#birelationalmatrix-sections-ictl) (EUMAS25b). Each
model has two relations on the same finite state set:

- `P` (`<=_P`): information order, a partial order (reflexive, transitive and
  antisymmetric, EUMAS25b Def. 1 and footnote 4); truth is monotone as knowledge grows.
- `R`: serial transition relation; path quantifiers range over infinite `R`-paths.

Path formulas (`X`, `U`, `R`) use standard CTL semantics on `R`-paths. Only
implication and negation are intuitionistic: `phi -> psi` is checked at all
`P`-refinements of the current state.

The paper's well-behaved frames satisfy the confluence constraints C1 and C2
between `P` and `R` (EUMAS25b Def. 1). See the [ICTL algorithm](../algorithms/ictl.md).

#### Standard syntax (state formulas)

- Boolean: the constant false, `/\`, `\/` and `->`. Implication is primitive and
  negation is defined from it, `not phi` = `phi -> false`, so the excluded middle
  does not hold.
- Path quantifiers: `E`, `A` over `R`-paths.
- Temporal: `X`, `U`, `R`. The paper has no `F` or `G`; VITAMIN adds them as
  sugar after `E` or `A`.

ICTL model checking is PTIME-complete and runs in time `O(|M|^2 * |phi|)` for a
finite birelational model `M` and a formula `phi` (EUMAS25b Theorem 4).

### Syntax

#### Supported syntax

- Quantifiers: `E` / `exist`, `A` / `forall`.
- Temporal: `X`, `U`, `R`; sugar `F` / `G`; the words `next`, `eventually`,
  `globally`, `always`, `until` and `release` ([word operators](#word-operators)).
- Boolean: `&&` / `and`, `||` / `or`, `!` / `not`, `->` / `implies`.
- Propositions: `[a-z][a-zA-Z0-9_]*` ([names and keywords](#names-and-keywords)). Path/temporal
  tokens (`E`, `A`, `X`, `F`, `G`, `U`, `R`, keywords) are lexed separately so
  forms such as `EX` / `AG` are operators, not atoms.

#### Formula examples

```text
EX e
EF e
AX e
AF e
AG (p -> EF q)
AG goal
E p R q
!(e -> h)
```

The model type is `BirelationalMatrix`, a `CGS` subclass; its cells are in
[BirelationalMatrix sections](file_formats.md#birelationalmatrix-sections-ictl).
How the checker computes each operator, and the C1/C2 model checks:
[ICTL algorithm](../algorithms/ictl.md).

<a id="iatl---intuitionistic-atl"></a>
## IATL (Intuitionistic ATL)

### Theoretical background

IATL (Intuitionistic ATL) extends ATL with intuitionistic propositional
connectives and dual coalition modalities over [BCGS](file_formats.md#bcgs-sections-iatl) models (Bozzelli et al.,
KR 2025). Each model combines:

- CGS transitions: joint action profiles (multi-agent moves).
- Partial order `P`: information refinement; intuitionistic truth is monotone along
  `P`. The model file holds it in a section named `Preorder`.

The coalition modalities are written `<A>` and `[A]` for the paper's `<<A>>` and
`[[A]]`:

- `<A> phi`: coalition `A` has a strategy enforcing `phi`.
- `[A] phi`: no strategy of `A` can prevent `phi`.

In the paper (Definition 2), a well-behaved BCGS satisfies the per-coalition
constraints C1 and C2 (contravariant simulation of coalition decisions along `P`).

On finitely-branching BCGS, perfect-recall and memoryless semantics coincide
(KR 2025 Theorem 5); the explicit checker uses memoryless coalition
[pre-images](../algorithms/index.md#overview).
IATL model checking is PTIME-complete and runs in time `O(|G|^2 * |phi|)` for a
finite BCGS `G` and a formula `phi` (KR 2025 Theorem 6).

### Syntax

#### Formula examples

```text
<1>G a
[1,2]F goal
<1,2> p U safe
<1>X p
[1]X p
!p
p -> q
```

The model type is `BCGS`, a `CGS` subclass: CGS `Transition` cells (joint
actions) plus a boolean `Preorder` section (see
[BCGS sections](file_formats.md#bcgs-sections-iatl)). How the checker
computes each operator, and the C1/C2 model checks:
[IATL algorithm](../algorithms/iatl.md).

<a id="tctl---timed-ctl"></a>
## TCTL

Timed CTL over [`timedCGS`](file_formats.md#timedcgs-sections) models.

The quantifiers are `A` and `E`, with `F`, `G`, `U` (no `X` or release).

Clocks and clock guards:

- Automaton clocks `X` from the model `Clocks` section.
- Formula clocks `J` via freeze `j.phi` (reset `j` to `0`).
- Guards: standalone `x <= 5` or attachment `phi : x <= c` on subformulas.

For example:

```text
AG a
EF crossing
EF (p : x<=1)
j.A(j<=7 U goal)
```

The model type is `timedCGS`. The zone graph and the fixpoints over regions:
[TCTL algorithm](../algorithms/tctl.md).

<a id="tol---timed-obstruction-logic"></a>
## TOL

Timed Obstruction Logic with demonic cost prefixes over `timedCGS`
models (AAMAS 2025). `{Jk} phi` holds when the Demon, deactivating at each step
outgoing transitions of total cost at most `k`, can make every remaining path
satisfy `phi`. The Demon is the player that disables moves or edges at a cost
([algorithm design](../algorithms/index.md#overview)).

The demonic prefix is `{Jk}` (paper notation `<k>`), where `k` is a non-negative
integer written without leading zeros: `{J0}` is valid and `{J01}` is rejected. With
`k = 0` the Demon can still disable edges of cost 0, so `{J0}` can differ from TCTL
`A` ([grade 0](../algorithms/tol.md#grade-0)).
For example:

```text
{J5}F a
{J10}G safe
{J3}(p U q)
j.{J5}(j<=7 U goal)
```

The temporal operators are `F`, `G`, `U`, `R`, `W` (paper) and `X` (VITAMIN extension).

The budget `k` is spent anew at each step: the Demon may deactivate
transitions whose costs add up to at most `k`, and the budget does not carry over
along the path. OL (`<Jk>`) reads its budget the
same way.

The freeze `j.phi` resets formula clock `j` to `0` at the current state.

The model type is `timedCGS`, the same as TCTL. How the checker computes each
operator: [TOL algorithm](../algorithms/tol.md).

<a id="empty-coalition-policy"></a>
## Empty and repeated coalition policy

Outside COTL, VITAMIN does not support an empty strategic coalition written as `<>`.
In ATL an empty coalition `<<>>` is the CTL universal path quantifier `A` (JACM 2002, p. 675), so `<> F p` would say what `AF p` already says.

The policy is to reject `<> ...` in every logic except COTL, whose legion of demons may be empty (`<><0>`). Table 4 gives the correct surface for each property:

**Table 4: Surface to use for each property.**

| Intent | Use | Do not use |
| :--- | :--- | :--- |
| Eventually on all paths (CTL) | `AF p` | `<> F p` |
| Strategic coalition (ATL) | `<1> F p`, `<1,2> G p` | `<> F p` |
| Linear path eventually (LTL) | `F p` | `<> F p` |
| Cost-limited strategy (OATL / RBATL) | `<1><5> F p` | `<> F p`, `<1> F p` without a budget or bound, `<1> <5> F p` |
| Capacity / strategy-bound (NatATL) | `<{1}, 5> F p` | `<> F p` |
| Capacity coalition (CapATL) | `<{1}> F p` | `<> F p` |
| IATL universal coalition | `[1] G p` | `[] G p` (empty `[]` rejected) |

Table 5 lists where the rejection is enforced, for the logics whose coalition form
differs; ATL*, NatATL_Recall, NatATLF, NatSL, ICTL, TCTL and TOL are not listed.
`<\s*>` stands for `<>` with or without spaces inside:

**Table 5: Where an empty coalition is rejected.**

| Logic | Coalition form | Empty coalition |
| :--- | :--- | :--- |
| ATL / ATLF | `<1>`, `<1,2>` | `<> ` rejected (precheck + parser) |
| IATL | `<1>` exist, `[1]` forall | `<> ` and `[]` rejected |
| NatATL | `<{1,2}, k>` | `<\s*>` rejected |
| CapATL | `<{1,2}>` | `<\s*>` rejected |
| OATL | `<1><5>` | `<\s*>` rejected; budget required |
| COTL | `<1,3><1>` | `<><0>` allowed (empty legion of demons); budget required |
| RBATL / RABATL | `<1><5>` or `<1><2,2>` | `<\s*>` rejected; bound required |
| OL | `<J5>` (Demon budget, no agents) | N/A |
| Wallet_ATL | `<<1>>` | `<<>>` invalid (lexer) |
| CTL / LTL | `E` / `A` or none | `<> ` invalid syntax |

VITAMIN also rejects a coalition that lists an agent twice, because a coalition is a set of agents (ATL, JACM 2002, rule S3: A "is a set of players").
This holds in every logic whose coalition lists agents, including IATL's `[A]` and COTL's list of demons (its legion).
For example, `<1,1> F p` in ATL and `<{2,1,2}> F p` in CapATL are errors that name the repeated agent.

<a id="names-and-keywords"></a>
## Names and keywords

This section is the one source for how names, reserved words and operator words
are written, in models and in formulas of every logic. Other docs link here.
Five rules cover it:

1. A name (proposition, clock, capacity) is `[a-z][a-zA-Z0-9_]*`, the same in
   models and formulas: `goal` and `goalA` are names, `P`, `Goal` and `GOAL` are
   errors (IATL, TCTL and TOL report `P` and `GOAL` as `Invalid character`).
2. The 17 [reserved words](#reserved-words) are never names, in any letter case.
3. A word operator such as `until` is an operator only in lowercase, and only in a
   logic that has the operator ([word operators](#word-operators)).
4. `true` and `false` are constants in lowercase only, in every logic.
5. Operator symbols (`F`, `U`, `AG`, and CapATL's knowledge operator `K1`, whose
   word form is `kcap1`) are uppercase only. With rule 1, a word that starts with an uppercase letter is
   never a name.

So each word has one reading. `p until q` is an Until. `p Until q` is an error,
because the parser meets `Until` where an operator must stand. `F Until` is an
error from the [reserved-word](#reserved-words) check, because `Until` stands where
a name must stand. `F Goal` gives "Atomic proposition 'Goal' is invalid", never a
proposition that is false everywhere.

### Names

Proposition, clock and capacity names follow rule 1 in a model and in a formula.
CGS action names (`A`, `block_a1`) and agent labels are not names in this sense and
may start with a capital.

- Pattern: `NAME_RE` in `model_checker/parsers/syntax_patterns.py`, a lowercase
  letter, then letters, digits or `_`.
- Formulas: `validate_proposition_identifier()` in
  `model_checker/parsers/formulas/parser_utils.py` checks, in every logic, the
  propositions of a formula, the capacity names of a CapATL formula and the clock
  names of a TCTL or TOL formula (in a freeze `x.phi` and a comparison `x<=2`).
- Models: `validate_model_name()` in
  `model_checker/parsers/game_structures/cgs/cgs_utils.py` applies the same check
  to the propositions of a CGS model, the `Clocks` section of a timedCGS model and
  the `Capacities` section of a capCGS model. So a model cannot declare a clock or
  capacity such as `Next` that no formula can name.

The message starts with the kind of name (`Atomic proposition`, `Clock` or
`Capacity`) and the word:

```text
Atomic proposition 'Goal' is invalid: a name starts with a lowercase letter, then letters, digits or _ ([a-z][a-zA-Z0-9_]*).
Atomic proposition 'Until' clashes with reserved keyword.
```

IATL, TCTL and TOL report an all-capital word such as `P` or `GOAL` as
`Invalid character` instead (see [lexer word patterns](#lexer-word-patterns)).

### Reserved words

Reserved words (any letter case): `and`, `or`, `not`, `implies`, `until`, `release`, `globally`, `next`, `eventually`, `always`, `forall`, `exist`, `weak`, `with`, `is`, `true`, `false`.

The list is `FORMULA_RESERVED_WORDS` in `model_checker/parsers/syntax_patterns.py`: every operator word of
the [word operators](#word-operators) table plus the two constants. A word is
reserved in every logic, even where the logic has no such operator (`weak` in ATL,
`with` outside TOL), so a name means the same in every logic, apart from `kcap` below.

CapATL alone also reserves `kcap` (any letter case), in its formulas and in capCGS
models, as a proposition or capacity name. Its parser reads `kcap` followed by
digits as the knowledge operator (`kcap1(...)` is `K1(...)`), so a capCGS model
also refuses `kcap1` or `kcap42` as a name; `kcap1x` is an ordinary name. Other
logics and plain CGS models accept `kcap` and `kcap1` as names.

`true` and `false` are the boolean constants, so a model that declares a proposition, clock or
capacity with either name (`true`, `True`, `FALSE`, ...) is rejected when it is read. In a
formula they are constants in lowercase, and `True` is a reserved-word error.

### Word operators

Most operators have a word form beside the symbol: `p until q` is `p U q`, with the
same precedence. Table 6 lists every word, the symbol it stands for and the
logics that read it. The words are `OPERATOR_WORDS` in `syntax_patterns.py`, which
feeds every parser except NatSL's (its goal pattern reads `not` only), so a word is
spelled the same in every logic that has it. In a logic that does not read a word,
or in another letter case ([rule 3](#names-and-keywords)), the word is an error. `p Until q` gives
"Syntax error near token 'Until'" in every logic except two: ATL* gives the
reserved-word message and NatSL "Unsupported goal". CapATL's `kcap1(...)` is not in
the table, because the word carries the agent number; see `kcap` under
[reserved words](#reserved-words).

**Table 6: Word operators, their symbols and the logics that read them.**

| Word | Symbol | Read by |
| :--- | :--- | :--- |
| `not` | `!` | every logic |
| `and` | `&&` | every logic except NatSL |
| `or` | `\|\|` | every logic except NatSL |
| `implies` | `->` | every logic except NatSL |
| `next` | `X` | every logic except NatSL, TCTL |
| `eventually` | `F` | every logic except NatSL |
| `globally` | `G` | every logic except NatSL |
| `always` | `G` | every logic except NatSL |
| `until` | `U` | every logic except NatSL |
| `release` | `R` | CapATL, COTL, IATL, ICTL, OATL, OL, TOL |
| `weak` | `W` | COTL, OATL, OL, TOL |
| `forall` | `A` | CTL, ICTL, TCTL |
| `exist` | `E` | CTL, ICTL, TCTL |
| `with` | `:` | TOL |
| `is` | `is` | CapATL |

NatSL reads `not` before its goal (`E{1}x: (x, 1) not F p`) and takes no other
word, because its goal is one operator and one proposition
([the NatSL reference](../algorithms/natsl.md)). TCTL writes its clock
constraint with `:` only. CapATL reads `is` only
inside its knowledge operator, `K1(1 is c)`, and it has no symbol besides the word.

### Operators glued to a name

An operator written with no space before a name, such as `Fp`, is one word that
[rule 1](#names-and-keywords) refuses, never the operator applied to the name. It fails in one of three ways:

- Every logic except NatSL reads `Fp` as one word and refuses it by name, with `Atomic proposition 'Fp' is invalid`.
- IATL, TCTL and TOL give `Invalid character 'F'` for a word that starts with two capitals, such as `FFuel`, then refuse the rest (`Atomic proposition 'Fuel' is invalid`), because their lexer reads only a capital followed by a lowercase letter as the start of a word.
- NatSL rejects it with "Unsupported goal", so `Fgoal` is an error. A lowercase operator (`f goal`) is also an error ([rule 5](#names-and-keywords)).

### Lexer word patterns

Each parser's lexer reads a word (a run of letters, digits and `_`) with a pattern
wider than the name rule, so that `Goal` or `Fp` is read as one word and refused by
name, instead of `Fp` being read as `F p`. Most patterns are constants in
`syntax_patterns.py`:

- Every logic except IATL, TCTL, TOL, ATL* and NatSL, ICTL included:
  `PROPOSITION_TOKEN` = `[a-zA-Z][a-zA-Z0-9_]*`, Wallet_ATL included. `_goal` is therefore an `Invalid character '_'` error.
- ATL*: its grammar's own `IDENT` = `[a-zA-Z_][a-zA-Z0-9_]*`, so `_goal` is
  read as one word and refused by name.
- IATL, TCTL and TOL: `ICTL_PROPOSITION_TOKEN` (also named
  `TCTL_TOL_PROPOSITION_TOKEN`) = `[a-z][a-zA-Z0-9_]*` or
  `[A-Z][a-z][a-zA-Z0-9_]*`, so that `AF` and `EX` stay operators. `Goal` is
  refused by name; an all-capital word such as `P` or `GOAL` is an
  `Invalid character` error.
- NatSL temporal atoms: read with `[A-Za-z_][A-Za-z0-9_.]*` in its goal pattern
  (`model_checker/parsers/formulas/NatSL/parser.py`), then checked with the name rule and the reserved-word rule; `true` and
  `false` are accepted as constants.

<a id="syntax-cards"></a>
## Syntax cards

Table 7 gives, for each logic, the prefix that scopes a formula, its temporal
operators as symbols, the model type it reads and one formula that parses. Word
forms are in [word operators](#word-operators), and the connectives and constants
in [Boolean logic](#boolean-logic-shared-syntax). The per-logic sections and
algorithm pages give the semantics. Each example parses; the NatSL one also checks
only on a 1-agent model (see [NatSL](#natsl---natural-strategy-logic)).

**Table 7: Syntax card of each logic.**

| Logic | Prefix | Operators | Model | Example |
| :--- | :--- | :--- | :--- | :--- |
| LTL | none | `X`, `F`, `G`, `U` | CGS | `G (p -> F q)` |
| CTL | `A`, `E` | `AX`, `AF`, `AG`, `EX`, `EF`, `EG`, `A[p U q]`, `E[p U q]` | CGS | `AG (p -> EF q)` |
| ICTL | `A`, `E` | as CTL, plus `R` in `A[p R q]`, `E[p R q]` | BirelationalMatrix | `E[p R q]` |
| TCTL | `A`, `E`; clock constraint `phi : x<5`; freeze `x.phi` | `AF`, `AG`, `EF`, `EG`, `A(p U q)`, `E(p U q)` (no brackets) | timedCGS | `AF p : x<5` |
| ATL | `<1,2>` | `X`, `F`, `G`, `U` | CGS | `<1,2>F p` |
| ATLF | `<1,2>` | `X`, `F`, `G`, `U` | fuzzyCGS | `<1>(p U q)` |
| IATL | `<1,2>` exists, `[1,2]` for all | `X`, `F`, `G`, `U`, `R` | BCGS | `[1,2]F goal` |
| ATL_STAR | `<<1,2>>` | `X`, `F`, `G`, `U`, nested path formulas | CGS | `<<1>> (F p && G q)` |
| Wallet_ATL | `<<1>>`, `<<1:wallet(1,>=10)>>` | `X`, `F`, `G`, `U` | WalletCGS | `<<1:wallet(1,>=10)>>F p` |
| OATL | `<1,2><10>` | `X`, `F`, `G`, `U`, `R`, `W` | costCGS | `<1,2><10> (p W q)` |
| COTL | `<1,2><1>`, `<><0>` | `X`, `WX`, `F`, `G`, `U`, `R`, `W` | ObstructionModel | `<1,2><1> G !q` |
| RBATL | `<1><10,5>` | `X`, `F`, `G`, `U` | costCGS | `<1><10,5>F p` |
| RABATL | `<1><2,2>` | `X`, `F`, `G`, `U` | costCGS | `<1><2,2>F p` |
| NatATL | `<{1,2}, 5>` | `X`, `F`, `G`, `U` | CGS | `<{1,2}, 5>F p` |
| NatATL_Recall | `<{1,2}, 5>` | `X`, `F`, `G`, `U` | CGS | `<{1}, 3>G p` |
| NatATLF | `<{1,2}, 5>` | `X`, `F`, `G`, `U` | CGS | `<{1,2}, 5>F p` |
| CapATL | `<{1,2}>`; knowledge `K1(...)` | `X`, `F`, `G`, `U`, `R` | capCGS | `<{1}>F (g && K1(1 is c))` |
| OL | `<J5>` | `X`, `F`, `G`, `U`, `R`, `W` | costCGS | `<J5> (p R q)` |
| TOL | `{J5}`; clock constraint `phi : x<5`; freeze `x.phi` | `X`, `F`, `G`, `U`, `R`, `W` | timedCGS | `{J5}F x.(p : x<5)` |
| NatSL | `E{1}x A{1}y: (x, 1)(y, 2)` | one goal: `F`, `G` or `X` | CGS | `E{1}x: (x, 1) F goal` |

<a id="summary-logic-comparison-matrix"></a>
## Logic comparison matrix

The prefix, operators and model type of each logic are in the
[syntax cards](#syntax-cards); Table 8 adds what the cards leave out, and the
algorithm pattern each checker follows. A pre-image is the set of states from which
one step can be forced into a given set; it and the other techniques are in
[algorithm design](../algorithms/index.md#overview). The path type is Linear when a formula
is read on one path (LTL) and Branching when every temporal operator sits under a
path quantifier, coalition, strategy quantifier or demonic prefix and the formula
holds at a state:

**Table 8: Path type, algorithm pattern and notes for each logic.**

| Logic | Path type | Algorithm pattern | Notes |
| :--- | :--- | :--- | :--- |
| CTL | Branching | Pre-image and fixpoints | Path quantifiers `A`, `E` |
| LTL | Linear | Strategy search and pruning | No prefix; true when all agents together have natural strategies of size at most 5 under which the formula, rewritten for CTL with `A` before each temporal operator, holds at the initial state ([LTL](../algorithms/ltl.md)) |
| ATL | Branching | Coalition pre-image and fixpoints | Coalition `<A>` with no bound |
| ATLF | Branching | Coalition pre-image and fixpoints | Per-state values, not a set of states ([ATLF](../algorithms/atlf.md)) |
| ATL* | Branching | LTL to deterministic parity automaton, product with the model, two-player game | Nested path formulas and coalitions inside `<<A>>`; no wallet guards |
| NatATL | Branching | Strategy search and pruning | Memoryless strategies; `k` is the strategy complexity |
| NatATL_Recall | Branching | Strategy search and pruning | As NatATL, with recall strategies |
| NatATLF | Branching | Strategy search and pruning | Delegates to the memoryless NatATL solver |
| NatSL | Branching | Strategy search and pruning | Schedule `space` (default) or `time` |
| OATL | Branching | Budget-aware coalition pre-image and fixpoints | Demon budget per step |
| OL | Branching | Budget-aware coalition pre-image and fixpoints (OATL with all agents) | Demon budget `<Jk>` per step |
| RBATL | Branching | Bound-aware coalition pre-image and fixpoints | Resource vector bound, flat action costs |
| RABATL | Branching | Bound-aware coalition pre-image and fixpoints | Resource vector bound, coalition-sum costs |
| CapATL | Branching | Coalition pre-image over capacity-restricted moves, and fixpoints | Knowledge operator `K1(...)` (the digit is the agent) |
| COTL | Branching | Legion one-step operators and fixpoints | Legion of demons, budget per step |
| Wallet_ATL | Branching | Coalition pre-image over payable moves, filtered by the wallet guards, and fixpoints | Wallet guards in the coalition |
| ICTL | Branching | Upward closure and pre-image fixpoints | Intuitionistic `->` and `not` |
| IATL | Branching | Upward closure and coalition pre-image fixpoints | Intuitionistic `->` and `!`; `[A]` is the universal coalition |
| TCTL | Branching | Zone graph and fixpoints over regions | Clock constraints and freeze |
| TOL | Branching | Zone graph and obstruction fixpoints | Per-step obstruction, clock constraints and freeze |

<a id="model-syntax"></a>
## Model syntax

Each logic reads one model type, given in its [syntax card](#syntax-cards). The
sections of every model type, how a loader detects the type, and examples are in
[file_formats.md](file_formats.md#supported-model-types):

- [CGS](file_formats.md#cgs-sections): the base concurrent game structure.
- [costCGS](file_formats.md#costcgs-sections): CGS with action or edge costs.
- [capCGS](file_formats.md#capcgs-sections): CGS with capacities.
- [fuzzyCGS](file_formats.md#fuzzycgs-sections): CGS whose labels are numbers
  between 0 and 1.
- [WalletCGS](file_formats.md#walletcgs-sections): CGS with one wallet per agent.
- [BirelationalMatrix](file_formats.md#birelationalmatrix-sections-ictl): ICTL's
  relation matrix.
- [BCGS](file_formats.md#bcgs-sections-iatl): CGS with a `Preorder` matrix.
- [timedCGS](file_formats.md#timedcgs-sections): costCGS with clocks.
- [ObstructionModel](file_formats.md#obstructionmodel-sections-cotl): COTL's graph
  with demons.
