# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [2.0.1] - 2026-11-18

Fixes for 2.0.0: model loading for CTL, TCTL, OL and TOL, RBATL coalition costs,
and two `IndexError` crashes. One change can alter results: in LTL, `!p U q` now
reads as `(!p) U q`; write `!(p U q)` for the negated Until.

### Fixed

- LTL: `!` binds tighter than `U`, as in Spot's precedence table (Spot-tl p. 15)
  and every other logic of the checker: `!p U q` is `(!p) U q`, no longer
  `!(p U q)`, and `X !p U q` is `(X !p) U q`. Breaking: a formula that meant
  the negated Until must now be written `!(p U q)`
  ([logic knowledge base](docs/reference/logic_knowledge_base.md)).
- LTL: `model_checking_wins_some_nash` and `model_checking_lose_some_nash` validate
  `target_agent` again (agent 0 read as the last agent; a number above the agent
  count raised `IndexError`).
- LTL: each `!` counts one in a condition's size, so `!p and !q` is 5, not 4
  ([LTL](docs/algorithms/ltl.md#how-a-check-runs)).
- RABATL: a `Costs_for_actions_split` row with too few costs is a `model` error
  naming the action, state and agent (it raised `IndexError` since 2.0.0).
- RBATL: a coalition move is affordable when one joint action is within the bound,
  not all, so other agents' costs are not charged to the coalition (PRIMA 2024
  pp. 5, 9); `<1><5,2> G !p` on `rbatl_2agents_8states_sensor.txt` holds in `s0`
  again. RABATL is unchanged ([RBATL](docs/algorithms/rbatl.md)).
- Loader: CTL, TCTL, OL and TOL no longer need a transition for every action
  combination, as OATL already did; a CTL or OL row such as `0 AC BD` was refused
  since 2.0.0 ([file formats](docs/reference/file_formats.md)).

## [2.0.0] - 2026-11-17

A major release: formulas and model files follow stricter rules (names start with
a lowercase letter, reserved words, one action per agent in a joint action, a
`Wallets` row and a `Clock_constraints` row for every state), and OL, LTL and
Wallet_ATL follow their papers. Read the "Breaking" entries before upgrading.

### Added

- CapATL evaluates the knowledge operator `Ka(...)` (AAMAS 2024 Def. 3.2): it holds
  when every complete capacity assignment agent `a` still considers possible,
  given the states and its own moves, satisfies the formula inside. Before,
  checking a formula with `K` returned a `validation` error. On the example model
  `capatl_3agents_3states_example.txt`, `<{1,2,3}> X K2(3 is cap)` holds in `q1`
  and `<{1,2}> F (K2(3 is cap) || K2(3 is cop))` in `q0` and `q1`. See
  [knowledge operator](docs/algorithms/capatl.md#knowledge-operator).
- CapATL: `a is c` with a capacity the model does not declare is a `semantic`
  error that names it.

- Model type `fuzzyCGS` (class `FuzzyCGS`) for ATLF: the CGS sections, with
  `Labelling` cells that are numbers between 0 and 1. See
  [fuzzyCGS sections](docs/reference/file_formats.md#fuzzycgs-sections).
- LTL `model_checking` takes the keyword arguments `k` (strategy size bound,
  default 5) and `agents` (the coalition, default every agent). Before, both were
  fixed. A `k` that is not an integer of at least 1, or an invalid coalition, is
  a validation error that names it. See
  [LTL algorithm](docs/algorithms/ltl.md#how-a-check-runs).
- LTL and NatATL reject an empty coalition, a coalition that names an agent twice
  and an agent number that is not an integer (such as `True` or `1.5`), with a
  validation error that shows the coalition or the number.

- ICTL accepts `A(p U q)`, `A[p U q]` and the Release forms, as the ICTL papers
  write them. Before, they were syntax errors.
- OL, TOL, RBATL, RABATL, CapATL and Wallet_ATL accept a parenthesized Until (and
  Release or Weak Until where the logic has them) after the prefix, such as
  `<J2> (p U q)` and `<1><5> (p U q)`. It builds the same tree as `prefix p U q`.
- Tests for operator spacing, Until forms and connective spelling in every logic,
  and one that keeps NatSL's "Unsupported goal" error for a connective in a goal.
- Docs: "Names and keywords" and "Syntax cards" in `logic_knowledge_base.md` are
  the one source for names, reserved words and each logic's syntax.
  `test_names_doc.py` checks them against the parsers.
- Docs: removed wrong examples and lists: `F`, `G` and `exists` as reserved words,
  `EF [p]` (CTL), `Ex : (x, 1) F goal` (NatSL), and `>`, `&`, `|` as ICTL
  connectives.

### Changed

- Breaking: TCTL `A` and `E` range over time-divergent paths only (Baier and
  Katoen, Def. 9.30, p. 701). A zero-time loop is no longer a path, and where
  time stops for good (a timelock) every `A` formula holds and every `E` formula
  fails. On `tctl_tol_minimal.txt`, `AF false`
  holds at `s0` and `EF p` fails there; on `tctl_zeno_cycle.txt`, `EG p` is
  false. TCTL graphs have more regions: 7 to 62 on the test models, against 4
  to 42. See [Time-divergent paths](docs/algorithms/tctl.md#time-divergent-paths).
- Breaking: TCTL `A(phi U psi)` is computed as `!(E(!psi U (!phi && !psi)) || EG !psi)`.
  Before, it held only where `psi` held: on `tol_cost_2states.txt`,
  `A (true U p)` gave `{s1}` while `AF p` gave `{s0, s1}`.
- Breaking: TOL lets a path stay where it is: every region has a time step of
  delay 0 to itself (AAMAS 2025, p. 4), so the Demon must keep that region inside
  the target too. Before, the last region before an invariant bound had no time
  step at all and counted for `{Jn} F` and `{Jn} U` as if every path from it
  reached the goal. On `tol_cost_2states.txt`, `{J2} F p` and `{J2} q U p` drop
  from `{s0, s1}` to `{s1}`: time may stand still at `s0`. Known limitation:
  since a path may stay in its region forever, `{Jn} F phi` gives exactly the
  regions of `phi` and `{Jn} (phi U psi)` those of `psi`, on every model. The
  paper's Algorithm 2 and Proposition 1 (p. 5) give the same result, its Theorem 2
  (p. 6) does not, and TOL keeps it. See
  [Obstruction step](docs/algorithms/tol.md#obstruction-step).
- Breaking: an error found while reading a model file (not UTF-8, or a format
  rule broken) has type `model` in every logic. Before, most came back as
  `system` (for example an ICTL or IATL preorder that is not reflexive, or rows
  of different lengths), a few as `semantic` (a proposition name such as `A` in
  `Atomic_propositions`) and, in NatSL, all as `validation`.
- Breaking: CapATL rejects a `Capacities_assignment` cell other than `0` or `1`,
  with an error that names it. Before, a value such as `2` loaded and was read
  as `0`.
- Breaking: RBATL and RABATL reject a bound with more values than the model's
  cost vectors, with a `validation` error that names the bound. Before, the extra
  values were ignored: `<1,2><3,1,5>F p` on a model with two resources gave the
  answer of `<1,2><3,1>F p`.
- Breaking: RBATL and RABATL keep a coalition move in the bounded pre-image only
  when every joint action that contains it lands in the target and costs at most
  the bound, as `Pre(C, X, b)` of Catta et al. (PRIMA 2024, p. 9) asks. Before,
  one joint action within the bound was enough and the other agents' choices
  were not checked. On `rbatl_3agents_medium_6states_costs.txt` for RABATL,
  `<1,2><0,0>F r` shrinks from `{s1, s2, s3, s4}` to `{s1, s3, s4}`: at `s2` the
  move `AA` has the completion `AA^` of cost 2. See
  [Bounded pre-image](docs/algorithms/rbatl.md#bounded-pre-image).
- NatATL (memoryless and recall): a bound `k` below the number of coalition
  members gives `Result: False`, since no profile of that size exists. Before,
  it was a validation error. See [Strategies](docs/algorithms/natatl.md#strategies).
- Breaking: the loader rejects a model where a state has no transition for some
  combination of the agents' available actions (the actions each agent plays in
  the state's row). The message names the state and up to three missing
  combinations. Before, a combination with no cell was treated as not available:
  in a row that lists only `AC` (to a `g` state) and `BD` (to a `!g` state), both
  `<1>X g` and `<2>X !g` held. OATL models and IATL (BCGS) models are exempt,
  because their papers make the transition function partial. NatSL reports the
  error at load time instead of its own "Non-total local joint-action table"
  message. See [Transition](docs/reference/file_formats.md#transition).
- NatATL and NatATLF report a formula error without the prefix "Invalid NatATL
  formula format:", as NatATL_Recall does: `<{1}, 1>F` gives "Invalid NatATL
  formula: Syntax error at end of input". The error type stays `syntax`.
- Test fixtures gained the missing combinations: the RBATL sensor fixture has the
  idle self-loops and `CC` of PRIMA 2024 Fig. 1, and in the three-agent RBATL and
  RABATL fixtures the added combinations keep the state at cost 0, so
  `<1><2>F r` gives `s1, s3, s4` (before `s0` to `s4`).
- Breaking: CapATL follows AAMAS 2024 (Def. 2.5, 2.9, 3.2). The coalition keeps
  one capacity per member for the whole strategy and does not see the opponents'
  moves; each opponent may play any of its capacities, one per play. Before, the
  checker picked one capacity for every agent, opponents included, and returned a
  state if one such choice won, and a `*` in a transition label matched no action
  of a coalition member. On the example model `capatl_3agents_3states_example.txt`,
  `<{1,2}>X g` gives `q0, q2` (before `q1`), `<{1,2,3}>X g` gives `q0, q1, q2`
  (before `q1`), `<{3}>X g` gives `q2` (before none), `<{1,2}>F g` gives
  `q0, q1, q2` (before `q1, q2`) and `<{1,2}>G a` gives `q0, q1, q2` (before none).
  The capCGS loader rejects a model whose `Capacities_assignment` does not have one
  row per agent and one column per capacity, where an agent has no capacity, or
  where an assigned capacity has no line in `Actions_for_capacities`. See
  [CapATL algorithm](docs/algorithms/capatl.md).
- Breaking: NatATL_Recall follows natural strategies with recall of AIJ 2019
  (section 6.1, p. 21). A rule's condition is a pattern over the history (the
  states visited so far). A plain condition `p` matches only the one-state history
  of a `p` state; `true* . p` matches every history ending in a `p` state, at the
  same size. Every rule list ends in `(true*, IDLE)`, which counts 1, and `k`
  bounds the sum over the coalition, as for NatATL; before, each member's list had
  size exactly `i` for `i = 1, ..., k`. Goals more than four steps away are found
  (the search was cut at depth 4), and a pattern applies on every history it
  matches (before, on one). See [Recall](docs/algorithms/natatl.md#recall).
- Breaking: TCTL and TOL work on the
  [region graph](docs/algorithms/tctl.md#region-graph) of IC 1993 (p. 20): each
  node is a location and a clock region, and regions never overlap. A clock
  constraint such as `x<=3` holds in a region only when it holds for every clock
  value there. Before, the nodes were zones (sets of clock values given by
  bounds), a constraint held in a zone if one clock value met it, and
  `AG (p : x<=3)` held on a location whose invariant lets time run to `x=10`.
  - A time step leads only to the next clock region. Before, it could skip the
    regions between, and `E (x<=3 U x>=5)` held where time runs through `3<x<5`.
  - The graph grows with the clock constants (the largest number each clock is
    compared with) and the number of clocks: the test models have 4 to 42
    regions, where they had 2 to 6 zones.
  - The pre-image of TCTL and TOL no longer keeps only regions that meet the
    operand's guard, so `EF (p : x>5)` and `AG !(p : x>5)` no longer both hold.
  - TOL works on regions of the region graph instead of locations. The Demon (the
    player that disables edges at a cost) cannot disable a time step, an edge
    counts only if it can be taken from the region, and the Demon may not disable
    every edge of a location. See
    [obstruction step](docs/algorithms/tol.md#obstruction-step).
  - TOL `res` lists only locations the region graph reaches, as TCTL does.
  - A freeze `j.phi` holds in a region when `phi` holds in the region reached by
    resetting `j` to 0 there (AAMAS 2025 Def. 11, p. 4; IC 1993 p. 22). TCTL and
    TOL used to evaluate `j.phi` as `phi` in effect, following AAMAS 2025
    Algorithm 1 (line 19, p. 5), which contradicts that paper's Def. 11, so a
    freeze under a temporal operator was wrong: on `tctl_invariant10_exit.txt`,
    `EF (x>8 && j.EF (p && j>=2))` held although time cannot advance by 2 at `s0`
    after `x>8`. `res` lists only locations of regions that
    time and edge steps reach from the start, not ones only a freeze reset leads
    to. See [TCTL overview](docs/algorithms/tctl.md#overview).
- Breaking: TCTL and TOL reject a freeze on a clock the model declares, such as
  `x.EF (x>=2)` with the model clock `x`, with a `semantic` error that names the
  clock (AAMAS 2025 Def. 10, p. 4, keeps the model's clocks and the formula's
  apart). Before, the freeze reset the model clock.
- Breaking: TOL rejects `X` and `next` (AAMAS 2025, p. 4, has no next operator).
- Breaking: NatATL (memoryless) and NatATLF use the natural strategies of AIJ 2019
  (section 4.1). See [NatATL strategies](docs/algorithms/natatl.md#strategies).
  - A strategy ends with a `(true, action)` rule, and each rule's action must be
    available wherever that rule is the first to hold.
  - A member plays exactly its rule's action. Before, it could also idle, and it
    idled in states no rule covered.
  - Conditions are any Boolean formula with `!`, `&&` and `||`. Rules may share an
    action, and their order matters.
  - `k` bounds the total size of the coalition's profile, `true` rules included; a
    `k` below the coalition size is a validation error. Before, each member's
    strategy had size exactly `i` at step `i`. `Complexity Bound` is the total
    size of the profile found.
  - A profile that leaves a state with no move is skipped.
  - The same `k` can give a different answer: `<{1}, 1>F p` on a model whose two
    states offer different actions is now false.
- Breaking: RBATL and RABATL bound the summed cost of the coalition's moves
  along a path, per resource, as PRIMA 2024 defines it (Def. 4). Before, the bound
  applied to each step on its own: on the chain test model `<1><1>F p` held at
  `s0`, although `p` is two steps of cost 1 away. `<1><b>G p` with `b > 0` holds
  only where `p` can be kept forever within the total. The Until also holds where
  `psi` holds and `phi` does not. A bound that needs more than 100000 budgets (the
  product of `b_i + 1`) is a validation error. See
  [RBATL operators](docs/algorithms/rbatl.md#operators).
- ATLF reads its model as `fuzzyCGS`, so labels such as `0.7` are accepted. The
  CGS loader accepts only 0 and 1, so before this change ATLF gave the same
  answers as ATL. Other logics still read a CGS. Benchmarks still generate CGS
  models for ATLF.
- Docs: algorithm, reference and guide pages, README and AIUSE are checked
  against the code and the papers, and their wrong statements are fixed.
- Docs: the [knowledge base](docs/reference/logic_knowledge_base.md#atl-star)
  gives the sources for reading ATL* `<<A>> p U q` as `<<A>> (p U q)`; no paper
  states this reading. A test checks the Until fixpoint law (FPU) written without
  parentheses.
- `birelational_matrix` is a package with an `__init__.py` exporting
  `BirelationalMatrix`, so it has an API page.
- RBATL and RABATL accept a bound of 0 (`<1><0,5>F p`): that resource then allows
  only moves of cost 0. Before, any 0 was an error, so a formula that nests
  `<1><0,0>`, such as the rover mission test, could not run.
- TOL accepts the grade `{J0}`: the Demon then disables only edges of cost 0.
  Before, `{J0}` was a syntax error. `{J01}` is rejected with a message that names
  it, as OL does for `<J01>`. See [grade 0](docs/algorithms/tol.md#grade-0).
- OL and OATL reject an edge or joint action whose cost adds up to 0 or less
  (`$0` in `Costs_for_actions`, or a `Transition_With_Costs` cell such as `0:0`,
  `00` or `-1`) with a model error that names it, as their papers require
  positive costs. Before, `<J0>` could disable such an edge, so it differed from
  CTL. Models with such an edge must give it a positive cost. A `*` self-loop in
  `Transition_With_Costs` was already an error; the message now ends with "write
  a self-loop as a cost on the diagonal". See
  [OL algorithm](docs/algorithms/ol.md#how-a-check-runs).
- OL checks a model with no `Initial_State` section and returns the states where
  the formula holds, with an empty `initial_state` field. Before, such a model was
  rejected with "Initial_State section is missing or empty". Other logics still
  require the section. A logic opts out through `"initial_state_required": False`
  in the `METADATA` of its formula package
  (`model_checker/parsers/formulas/OL/__init__.py`).
- Breaking, compared with the original VITAMIN repository (commit e8ea8773).
  Formulas or models written for that code can give other results in these
  cases:
  - Connectives have a precedence, `!` before `&&` before `||` before `->`, and
    `->` groups to the right. The original parsers had no precedence table and
    grouped to the right of each connective: `!p && q` was `!(p && q)`, `!p || q`
    was `!(p || q)`, `p && q || r` was `p && (q || r)` and `p && q -> r` was
    `p && (q -> r)`. They now read `(!p) && q`, `(!p) || q`, `(p && q) || r` and
    `(p && q) -> r`. See
    [Boolean logic](docs/reference/logic_knowledge_base.md#boolean-logic-shared-syntax).
  - A state with no successor (a `Transition` row of only `0`) is a load error
    ("Model structure validation failed: ...") that names the state and suggests a `*` self-loop. The original loaded such a
    model, and its CTL and ATL read the state in different ways. In CTL, `AX phi`
    held there whatever `phi` was, `EX phi` and `EG phi` failed, `AG phi` and
    `EF phi` held exactly where `phi` did, and `AF phi` was computed as `AG phi`.
    In ATL, every `<A>X phi` failed there, so `<1>X q` and `<2>X !q` both failed
    at the same state. See
    [CGS sections](docs/reference/file_formats.md#cgs-sections).
  - NatATL, NatATLF, LTL and SolutionConcepts can build a strategy rule whose
    action is idle (`I`), as AIJ 2019 does (p. 13). The original left `I` out of
    the actions it built rules from, so a check of a coalition with bound `k` can
    change from false to true. Example: two agents and three states; `s0` moves
    to `s1` on `II`; `s1` stays on `II` and moves to `s2`, where `r` holds, on
    `bI`; `s2` loops on `II`. LTL `G !r` with `k = 1` holds at `s0`, because
    agent 1 can idle in `s1`; the original gave false.
- Docs: [NatATLF](docs/algorithms/natatlf.md#relation-to-humanatlf) is NatATL on
  labels 0 and 1. It is not HumanATL[F] of AAAI 2026, whose code is in
  HumanATLFTool.
  [NatSL](docs/algorithms/natsl.md#fragment-covered) covers the one-goal,
  non-alternating fragment of SPIRIT 2024 (p. 5).
  [Wallet_ATL](docs/algorithms/wallet_atl.md#two-readings-of-the-guard-in-the-paper)
  gives the paper's two readings of where a guard holds (Def. 4.5 and
  Algorithm 1) and an example where they differ. The knowledge base says that
  `->` groups to the right, as in NuSMV and Spot, and why a Wallet_ATL guard must
  name a coalition agent. OL and the file formats page say how a `*` cell of
  `Transition` gets its cost.

- Docs: pages are grouped under `docs/algorithms/` (one page per logic plus
  `index.md`), `docs/reference/`, `docs/guides/` and `docs/examples/`. The old
  `docs/<LOGIC>/algorithm.md` paths are gone.
- RBATL and RABATL reject a bound with a leading zero (`<1><05>F p`,
  `<1><2,05>F p`) with OATL's message "Bound cannot have leading zeros". Before,
  `<1><05>` was read as 5.
- Syntax errors name a word operator as written: `<J1> weak p` in OL gives "Syntax
  error near token 'weak'" (it said 'W'). In CTL, a temporal operator with no
  quantifier gets "must be preceded by a quantifier" also when written as a word
  (`p until q`, `eventually p`) or when the formula has a proposition named `a` or
  `e` (`a U p`); both were syntax errors. Every parser reads the word spellings
  from one table, `OPERATOR_WORDS` in `syntax_patterns.py`.
- Breaking: in CapATL, `kcap` is a reserved word in any letter case, because
  `kcap1(...)` is the knowledge operator. `<{1}> F kcap` gets "Atomic proposition
  'kcap' clashes with reserved keyword." and `K1(1 is kcap)` gets "Capacity 'kcap'
  clashes with reserved keyword.". A CapCGS file that declares `kcap` as a
  proposition or capacity is refused at load, and so is a capacity named `kcap`
  plus digits (`kcap1`): "Capacity 'kcap1' spells the CapATL knowledge operator
  (kcap1(...)), so no formula could name it." `kcap1x` stays a name. Other logics
  and plain CGS models keep `kcap` and `kcap1`. No model file here or in the
  Workbench uses them.
- OATL, RBATL and RABATL name a missing bound for any coalition without one, such
  as `<1> eventually p` or `(<1><5>F p) && (<2> F q)`: OATL gives "Temporal
  operators require a bound ...", RBATL and RABATL "RBATL requires a resource bound
  ...". Before, only a symbol operator right after the coalition (`<1> F p`) got
  that message; the rest got "Invalid character" for `<`. OATL also names a
  leading-zero bound before a word operator and in any coalition
  (`<1><05> eventually p`). A space between coalition and bound (`<1> <5>F p`) is
  an error in all three: "The bound follows its coalition with no space: write
  <1><5>, not <1> <5>" (before, "Invalid character '<'").
- Breaking: a WalletCGS file needs a `Wallets` row for every state (AAMAS 2026,
  Def. 3.1). Before, a state with no row held 0 for every agent; loading now fails
  with `Wallets has no row for state(s) s1; ...`. To keep the old result, add a row
  of zeros.
- Breaking: CTL with `generate_trace=True` always returns the full result (`res`,
  `initial_state`, `satisfied`, `states`, `trace`, `strategy`, `metadata`), and
  `trace` is `None` for a false E-operator (`EX`, `EF`, `EG`, `EU`), a true
  A-operator (`AX`, `AF`, `AG`, `AU`), a boolean connective or an atom. Before,
  every formula got a trace, so code reading `result["trace"]["states"]` must
  handle `None`.
- Breaking: every logic spells connectives `&&`, `||`, `!`, `->` or `and`, `or`,
  `not`, `implies`. A single `&` or `|`, and `>` as implication, give "Invalid
  character". Before, ATL*, TCTL and TOL took `&` and `|`, Wallet_ATL also `>`, and
  the other logics gave a bare "Syntax error".
- Breaking: in every logic with a prefix (coalition, path quantifier, bound or
  freeze), a connective after a prefix that no parenthesis closes is a syntax error
  giving the position and both readings: `<1>F p && q`, `<1> p U q && r`,
  `AF p && q`, `!<1>X p && q`. Write `(<1>F p) && q` or `<1>F (p && q)`. No
  defining paper states the grouping. Before, most logics read `(<1>F p) && q`,
  while TCTL and TOL read `A (p U (q && r))`.
- Breaking: a temporal operator is a word of its own in every logic, so `Xp` is one
  name, not `X p`. One-letter operators are uppercase only (`f p` and `p u q` are
  rejected; `until` and `eventually` still work), and a binary operator needs a
  space on both sides: `pUq` is one name, `pU q` and `p Uq` are errors.
  - LTL: `Xp`, `FGp`, `AXp`, `AGAFp` and similar, in either case, are names and
    `ltl_to_ctl` no longer splits them; write `X p`, `F G p`, `AX p`, `AG AF p`.
    `pUq` is a name too (before, rewritten to `A(p U q)`); write `p U q`.
  - LTL: an undeclared name is an error naming it ("Proposition(s) 'Goal' not
    among the model's declared propositions [...]"). Before, only all-lowercase
    names were checked, so `Goal`, `p1` and `pUq` were silently false.
  - NatSL: the goal needs a space after its operator (`F goal`); `Fgoal` and a goal
    with no operator (`Goal`) are rejected. `F`, `G`, `X` are uppercase and `not`
    lowercase: `f goal` and `NOT F goal` are rejected (case was ignored before). The
    normalised formula reads `...:(x,1)F goal`.
  - NatATL, NatATL_Recall and NatATLF: `<{1},1>Fa` and `<{1},1>fa` are rejected;
    write `<{1},1>F a`.
- Breaking: CTL takes square brackets only around an Until, `A[p U q]`, as Clarke,
  Emerson and Sistla (1986, p. 246) write it. Before, `[p] && q` and `AF [p]`
  parsed with the brackets as parentheses.
- Breaking: ATL* reads `<<1>> p U q` as `<<1>> (p U q)`, as ATL writes its Until
  (JACM 2002, pp. 685, 689; no paper states the reading, see the
  [knowledge base](docs/reference/logic_knowledge_base.md#atl-star)). A chained `U` (`p U q U r`), a `U` next to `&&`, `||` or
  `->` (`<<1>> (p U q && r)`) and any connective after a coalition
  (`<<1>> p && q`) are syntax errors asking for parentheses. Before,
  `<<1>> p U q` parsed as `(<<1>> p) U q` and failed with "a bare Until is not a
  state formula", and the other forms followed Spot's LTL precedence.
- Breaking: ATL* reads word operators in lowercase only, as the other logics do,
  and checks names by the same rule. `NOT p`, `p Until q`, `<<1>> Always p` and
  `<<1>> F True` are errors such as `Atomic proposition 'Until' clashes with
  reserved keyword.`; before, words matched in any case. `exist`, `forall`,
  `release` and `_goal` are no longer proposition names.
- Breaking: `weak`, `with` and `is` are reserved words in every logic and model, in
  any letter case. A model that declares one fails to load, and LTL `F weak` or OL
  `<J1> F With` fail with `Atomic proposition 'weak' clashes with reserved
  keyword.`; where the lowercase word is an operator (OATL `<1><2> F weak`) it is
  a syntax error. Before, most logics and all models accepted them as names. CapATL
  reads `is` in lowercase only: `K1(1 IS c)` is a syntax error.
- Breaking: a name starts with a lowercase letter, then letters, digits or `_`
  (`goal`, `goalA`, `safe_1`). This holds for propositions in every logic and
  model, clocks in a TCTL or TOL formula (`x.phi`, `x<=2`) or the `Clocks` section
  of a TimedCGS model, and capacities in a CapATL formula (`K1(1 is c)`) or the
  `Capacities` section of a CapCGS model. Before, a name could start with any
  letter, and a model clock or capacity could be a reserved word such as `next` or
  `with`.
  - `F Goal`, `AF P` and a model proposition `GOAL` fail with `Atomic proposition
    'Goal' is invalid: a name starts with a lowercase letter, ...`; a clock or
    capacity gets `Clock 'Goal'` or `Capacity 'Goal'`.
  - IATL, TCTL and TOL refuse `Goal` the same way but report an all-capital word
    (`P`, `GOAL`) as `Invalid character 'P'`.
  - `Fp` is one word starting with a capital, so it is an error, never `F p`.
- Breaking: NatATL, NatATL_Recall and NatATLF reject a bound `k` below 1
  (`<{1}, 0>F p`) with "Invalid bound 0: must be at least 1". Before, `k = 0`
  parsed and the solver returned false for every formula.
- TCTL rejects the next operator (`X p`, `AX p`, `EX p`, `A next p`) with "TCTL has
  no next operator ('AX' at position 1): time is dense, so there is no unique next
  state" (Alur, Courcoubetis, Dill 1993, p. 10). Before, "Syntax error near token
  'X'". Names such as `xray` still parse.
- Tests: a performance case with a `max_time` is stopped by pytest-timeout at 3x
  that time, set in the performance `conftest.py`. Before, the thread-based
  timeout waited for the hung call to finish, so a hang blocked the run, and the
  CapATL and NatATL cases had no timeout. The `performance` marker now applies
  (`pytestmark` in a conftest had no effect).
- Tests: the `e2e/` folder is removed (its three tests repeated integration tests),
  and so are markers no test used (`slow`, `e2e` and others), so `make test` no
  longer filters with `-m "not slow"`. The test `README.md` states what a test must
  assert to be kept.
- Tests: formula parser tests check each shared rule once over every logic:
  reserved words and names, coalition checks, connective precedence, word
  operators, and an operator with no operand. Eleven files that repeated these
  checks for a few logics are merged or removed.
- Tests: model file tests assert exact results. Every broken fixture in
  `tests/fixtures/tests/` is checked for its message, every valid fixture must load,
  and `BitVectorStateSet` is compared with a Python `set` on random inputs. Seven
  files that repeated each other or checked only types are merged or removed.
- Tests: algorithm unit tests compare with results worked out by hand: an opponent
  who can escape, a joint action with two outcomes, the bit vector path at 300
  states, cost bounds that remove a move in RBATL and RABATL, the trace length
  limit, and every ICTL and IATL frame check. Tests that recomputed the code's own
  formula, checked only types, or tested CTL release handlers no formula reaches
  are removed.
- Tests: automata tests check that the sink added by `complete()` loses under
  Büchi, co-Büchi and all four parity orientations, and compare both solvers with
  hand-computed winning regions. The attractor oracle moves from
  `model_checker/automata/games/_attractor_oracle.py` to
  `model_checker/tests/helpers/attractor_oracle.py`, so it no longer ships in the
  package. Tests of enum members, dataclass defaults and import wiring are removed.
- Tests: CTL, ATL and ATL* each have one semantics file with expected state sets
  worked out from the model (CTL's eight files and ATL's three become two and
  one). The new `test_error_contract.py` runs every registered logic on a valid
  formula, a formula cut short, an undeclared proposition and an agent the model
  lacks. CTL trace tests check the trace type and that the path follows real edges.

### Fixed

- CTL, TCTL, TOL and ATL* read a `*` cell of `Transition` as a transition to the
  cell's column, as ATL and the [file format](docs/reference/file_formats.md#transition)
  do. Before, they read a `*` off the diagonal as a self-loop on the row's state.
  On the Workbench model `ctl_train_controller_1agent_8states.txt`, whose `s7` row
  has `*` towards `sI`, `AG hazard` held at `s7` and holds at no state.
- ICTL reads a `*` cell off the diagonal as an `R` transition to the cell's
  column, as CTL, TCTL, TOL and ATL* do. Before, it was a self-loop on the row
  state, so in a model whose only move from `s0` to `s1` is a `*`, `EX p` with
  `p` at `s1` missed `s0`.
- ICTL rejects a `Transition` cell other than `0`, `R`, `P`, `P,R` and `*`, with
  an error that names it. Before, a cell such as `Q` loaded and counted as a
  transition for the checker but not for the serial and confluence checks.
- NatATL_Recall accepts a rule whose action is idle: it compared the model's `I`
  with the rule's `IDLE` and never matched, and it treated the tree's cut-off leaves
  as states with no action, so every rule failed (`<{1},1>G !r` was false on a model
  where idling keeps away from `r`). It reads a member's action at its agent
  number, not at its position in the coalition, and tries strategies in a fixed
  order. See [Recall](docs/algorithms/natatl.md#recall).
- NatATL_Recall accepts a model whose first state has only a self-loop while
  another state has transitions. It rejected such a model with "Configuration
  error: State 's0' has no transitions to other states", a limit of the tree it
  used to build from `s0`; histories start in any state.
- LTL conditions can negate any atom (`p and !q`); before, `!` could only stand on
  the first atom. The condition generator also uses every connective it is given
  instead of the first one; LTL still passes `and` only. See
  [LTL algorithm](docs/algorithms/ltl.md#how-a-check-runs).
- ATLF rounds `1 - x` to 12 decimals: `!p` with `p = 0.7` is `0.3`, not
  `0.30000000000000004`. Every value in its result is a float, so a state at 0
  prints `0.0`, not `0`.

- Every logic that answers with a state set prints `res` as a tuple in natural
  order, numbers inside a name compared as numbers: `Result: ('s1', 's2', 's10')`.
  Before, TOL, TCTL, CapATL, ATL*, IATL and ICTL printed a set whose order could
  change between runs (`Result: {'s2', 's0'}`), and the other logics sorted by text
  (`s10` before `s2`).
- timedCGS: `Clock_constraints` needs one row per state with one cell per state, and
  a guard or reset on a clock not in `Clocks` is an error naming the clock, row and
  column. Before, a short row or a missing row left cells empty, a long row failed
  with `IndexError`, and an unknown clock was kept. A model written with one cell
  per row for two states (`x<=1`) now needs `x<=1 0`.
- timedCGS: `Clocks` may span several lines (before, each line replaced the
  clocks of the one above), and a clock declared twice is an error naming it.
- WalletCGS: a `Wallets` row for an undeclared state, a repeated row, or a balance
  that is not a natural number (`abc`, `5x`, `-5`, `1.5`) is an error naming the
  value and the line. Before, a bad balance was dropped and a repeated row replaced
  the first. Comment and blank lines inside `Wallets` are skipped.
- costCGS and timedCGS: a cost for a state not in `Name_State` is an error naming
  the state and the action. Before, it was kept and never used.
- costCGS: `Costs_for_actions` after `Transition` is no longer read as transition
  rows, and `#` and `//` lines inside `Transition` are skipped.
- costCGS: a third token on a cost line and a negative cost are errors naming the
  value and the line. Before, the token was dropped and the cost kept.
- Joint actions: a profile with more actions than `Number_of_agents` (`AC` with 1
  agent) is an error naming the cell, in every checker that reads actions (CTL does
  not). Before, it was cut silently. NatATL and LTL queries on a coalition smaller
  than all agents give the same results.
- Model files: `Atomic_propositions` without a `Labelling` section is a structure
  error naming the propositions, in every model type. Before, every proposition
  loaded as false.
- `parse_state_set_literal` raises `ValueError` naming the value for an unparsable
  string (`{'s0', 's1'`) or a non-set, list or tuple (`42`). Before, both gave the
  empty set.
- `state_names_to_indices`, `state_indices_to_names` and `BitVectorStateSet`
  (constructor and `add`) raise `IndexError` naming an unknown state or an index
  outside `0..n-1`. Before, they skipped it. `remove`, `discard` and `in` still
  accept any index.
- Model type detection: a `//` line in the `Transition` section of an ICTL matrix
  made the file load as a CGS. It is now skipped like `#`.
- OATL, RBATL and RABATL: `<1><-5>F p` said "Negative agent indices are not
  allowed"; it now says "Bound must not be negative". `<-1>F p` keeps the agent
  message.
- ATL*: a formula nested about 140 levels deep (2000 nested `<<1>> F` or 2000
  parentheses) raised `RecursionError`. It now gives "Formula is nested too deeply
  to parse". The depth limit is unchanged.
- RABATL error messages (Release or Weak Until rejected, missing resource bound)
  said "RBATL"; they now say RABATL.
- LTL: `F false`, `F (p && !p)` and `F (p && q)` gave `Result: True` when the
  operand holds in no state. A rule whose condition holds nowhere meant "idle
  everywhere", which removed every transition of a model with no idle action. Now
  such a rule selects nothing, a state follows the first rule that holds there
  (before, a later rule could also cut it), and a profile that leaves a state with
  no successor is not admissible.
- NatATL (memoryless and recall) and NatATLF accept a connective between
  coalition formulas, such as `(<{1},1>F p) && (<{2},3>G q)` or `p and <{2},3>F q`.
  Before, a coalition formula left of `&&` failed (the CTL text `(A F p && A G q)`
  is ambiguous), and `and`, `or` and `implies` failed everywhere. The CTL text now
  parenthesizes each operand: `((A F p) && (A G q))`.
- Wallet_ATL accepts `true` and `false` as every other logic does: `<<1>>F true`
  holds everywhere and `<<1>>F false` nowhere. Before, they gave "Syntax error in
  formula" from a redundant post-parse check, now removed. `True` and `FALSE`
  stay errors (reserved words).
- TOL reads `release` and `weak` as `R` and `W`, as OL does: `{J1} p release q`
  builds the same tree as `{J1} p R q`. Before, both words were syntax errors.
- RBATL and RABATL report `<1><5> p Weak q` as a syntax error, as every logic does
  for a word operator not in lowercase. Before, `Weak` and `RELEASE` got "does not
  support Release (R) or Weak Until (W) operators".
- Wallet_ATL ignored some guards: one on an agent outside the coalition
  (`<<1:wallet(2, >= 100)>>X goal`), and all but the last on the same agent
  (`wallet(1, >= 100) && wallet(1, >= 5)` checked only `>= 5`). A guard outside the
  coalition is now a syntax error naming the agent, and every guard must hold, so
  `wallet(1, >= 3) && wallet(1, <= 5)` is a range. An exception while checking a
  guard now reaches the user instead of meaning "guard fails".
- Wallet_ATL X, F and U also required the guard at the successor state, so
  `<<1:wallet(1, >= 10)>>X goal` was false at a state holding 10 whose successor
  holds 5. They now follow Algorithm 1 of the Wallet ATL paper (AAMAS 2026, lines
  9 and 18-25): a state where `goal` holds counts for F and U even if the guard
  fails there. See [Wallet_ATL operators](docs/Wallet_ATL/algorithm.md#operators).
- Wallet_ATL ignored wallets when it built the coalition's moves, so an agent with
  5 could win through a `D20` move; the paper (Def. 3.1 and 4.1) makes
  `<<1>>X goal` false. The pre-image now uses only moves every agent can pay for,
  and a state with no affordable move is an error naming the state.
- WalletCGS: an income action no longer needs funds in the last agent's wallet.
  The paper allows income and neutral actions always.
- ICTL, IATL and ATLF: `true` and `false` were rejected ("does not evaluate the
  constant"). They now mean all states and no state (in ATLF, 1 and 0 everywhere).
- `true` and `false` are reserved words, so a model that declares a proposition
  with either name (any letter case) is rejected. Before, `<1>F true` used the
  constant and ignored the model's proposition.
- RBATL, RABATL and Wallet_ATL: when the initial state was False, the result was
  the state set of plain ATL, which is too large (RBATL `<1><1>G r` on the 6-state
  fixture listed s1, s3 and s4 instead of none), and an invalid bound such as
  `<1><0>G r` was accepted. The ATL prefilter is removed; the full check always
  runs.
- CapATL: a proposition name with a letter and a digit (`p1`) was read as a
  capacity reference and rejected as unknown. Every leaf is now a proposition name.
  Capacities are written `a is c` inside `K`, as the docs say.
- timedCGS: a strict invariant such as `x<3` was applied as `x<=3` (the parser
  dropped the operator). Time now stops before the bound.
- OL follows its paper (ECAI 2023, Definitions 3-4). In `<Jk> phi` a Demon, at each
  step, disables edges of the current state whose costs sum to at most `k`, never
  all of them, and every remaining path must satisfy `phi`. Before, `k` limited the
  total cost of the cheapest path, which the paper does not define, and `W` swapped
  the two arguments of `R`. For example, `<J26> F goal` on
  `ol_testvitamin_2agents_8states.txt` was False although the only path from state
  0 reaches goal. OL runs the OATL operators with the coalition of all agents
  (AAMAS 2024, section 6). `<J0>` is valid (the bound is in N0), `<J01>` is
  refused. `Transition_With_Costs` models give each cell as one edge with its cost.
  OL results in the VITAMIN Workbench change; the Workbench is updated in its own
  repository.
- OATL: a missing action cost that decides a result is a `model` error, not
  `system`. A coalition other than all agents on a `Transition_With_Costs` model is
  a `model` error, since such a model has no joint actions.
- TCTL and TOL: a name the model does not declare is a semantic error naming it.
  Before, it was a proposition false everywhere, so `AG !zz` held. LTL's Nash and
  sure-win functions (`model_checking_sure_win`, `model_checking_exists_nash` and
  the others that call `initialize`) check names too; before, `F zz` gave a
  verdict. NatATLF reports an undeclared name as `semantic`, not `system`; LTL as
  `semantic`, not `validation`; NatATL, NatATL_Recall and NatATLF name it in the
  message.
- Every logic names an undeclared proposition in its error ("Proposition(s) 'zz'
  not among the model's declared propositions [...]"). Before, ATL, ATLF, CTL,
  CapATL, COTL, IATL, ICTL, OATL, OL, RABATL, RBATL and Wallet_ATL said only that
  the atom does not exist, and IATL and ICTL called it a syntax error. A constant
  the logic does not evaluate (`true` in ICTL, IATL, ATLF) is named as such.
- LTL: `res` reads `Result: True` or `Result: False`, as in NatATL. Before, it was
  the literal text `Result: {satisfied}` or `Result: {}`.
- LTL, NatATL, NatATL_Recall and NatATLF refuse a model proposition named `A`, `E`,
  `AF` or another name the CTL parser reads as an operator, with a semantic error
  naming it. Before, they gave wrong verdicts: these logics check through CTL text,
  and a failed inner CTL check was read as "holds nowhere" or as a False goal. A
  failed inner CTL check now raises.
- ATL*: a proposition whose name starts with a Spot operator letter (`Granted`,
  `Fuel`, `Xray`) gave a wrong verdict or "RuntimeError: unimplemented", because
  Spot read `Granted` as `G(ranted)`. Names are now quoted in the text passed to
  Spot.
- CapATL: the knowledge operator K^a_cap (AAMAS 2024, p. 125-126) parses, as
  `K1(1 is c)` or `kcap1(1 is c)`, alone or inside a formula such as
  `<{1}> F (g && K2(3 is c || 3 is cop))`. Inside the parentheses only
  `agent is capacity`, `!`, `&&`, `||`, `->`, `true` and `false` are allowed. A `K1`
  without parentheses, a nested `K`, a proposition inside it and an agent out of
  range are errors naming the part. Before, `K1` was read as a proposition name and
  `K 1 (1 is c)` gave no result and no error. The solver has no K semantics yet:
  model checking a K formula returns a `validation` error ("The knowledge operator
  K1(...) is parsed but not evaluated by the CapATL solver yet").
- LTL: `ltl_to_ctl` is built from the parsed formula, not by regex. Before,
  `p U !q` was left unrewritten, and `p U q U r` became the left-grouped
  `A(A(p U q) U r)` although the parser groups to the right; it is now
  `A(p U A(q U r))`. Nested operands such as `((a && b)) U c` work. A formula the
  parser rejects raises a `ValueError` naming it, not passed on unchanged.
- NatATL, NatATL_Recall and NatATLF: a word starting with `F`, `G`, `X` or `U`
  (`Fuel`, `Goal`) is read as one word, so `<{1},1>F Fuel` is refused by the name
  rule (names start lowercase, see Changed). Before, it was read as an operator
  plus the rest of the name and failed with a CTL syntax error.
- timedCGS: a `#` or `//` line inside `Clocks`, `Clock_constraints` or
  `Invariants` is skipped, as in every other section. Before, it was read as a row
  and failed with "Malformed clock constraint" or "Malformed invariant", or a
  comment after the clocks replaced them.
- The PyPI package includes `model_checker/knowledge/knowledge_bundle.json.gz`,
  rebuilt from the current docs and source. Earlier releases left it out.
- CTL traces (`generate_trace=True`) were always the initial state alone. Now:
  - a true `EX`, `EF` or `EU` gives a witness path to a state satisfying the
    operand, and a true `EG` a witness lasso;
  - a false `AX` or `AG` gives a counterexample path to a state violating the
    operand, a false `AF` a counterexample lasso, and a false `AU` a path or a
    lasso.
  A lasso has the fewest states of any lasso. `trace["states"]` lists each state
  once, and the new key `trace["cycle_start_index"]` is the index its last state
  steps back to (`None` for a path).
- CTL with `generate_trace=True` printed `res` as an unordered set
  (`Result: {'s3', 's0'}`). It is now the sorted tuple the result without a trace
  prints (`Result: ('s0', 's3')`).
- RBATL and RABATL rejected a proposition ending in `weak` or `release`
  (`<1><5>F p_weak`, `<1><5>F isweak`) as an unsupported operator. Only `R`, `W`
  and the whole words `release` and `weak` are rejected now.
- NatSL goals accepted reserved words and a leading underscore as proposition names
  (`F or`, `F next`, `F True`, `F _p`), which a model cannot declare. The goal name
  now follows the rule of every other logic: a letter, then letters, digits or
  `_`, and no reserved word. `true` and `false` are constants: `E{1}x: (x, 1) F
  true` holds and `F false` does not. Before, they were unknown propositions.
- ATL, ATLF, IATL, CapATL, OATL, RBATL, RABATL, NatATL, NatATL_Recall, NatATLF and
  Wallet_ATL accepted a coalition listing an agent twice (`<1,1>F p`,
  `<<2,1,2>>F p`). It is now an error naming the agent (`Duplicate agent 2 in
  coalition`); ATL* and COTL already rejected it.
- COTL's legion errors use the wording of the other logics, with `demon`:
  `Duplicate demon 2 in coalition` and `Invalid coalition value 3: must be between
  1 and 2`.
- ATL* read `always` as a proposition name, so `<<1>> always p` was a syntax error
  and `<<1>> F always` parsed. `always` is the word for `G`, as in the other
  logics, and a reserved word.
- Reserved words are case-insensitive as proposition names. ATL, ATLF, CTL, LTL,
  ICTL, IATL, CapATL, COTL, OATL, OL, RBATL, RABATL, NatATL, NatATL_Recall and
  NatATLF accepted `<1>F Globally`, `AF NOT` and `AF Forall`; TCTL and TOL
  accepted `AF Always`, `AF True`, `AF release` and `{J1}F forall` (but not
  `AF until`). All are rejected now, as is a CapATL capacity such as
  `K1(1 is Next)`.
- A reserved word used as a proposition or capacity name failed with an empty
  error list. The parse now fails with `Atomic proposition 'Globally' clashes with
  reserved keyword.` (`Capacity 'Next' ...` for CapATL).
- TCTL and TOL accepted a reserved word as a clock name in a freeze (`Next.AF p`)
  or a comparison (`AF p : Weak<=2`, `{J1}F p with Release<=2`). The parse now fails
  with `Clock 'Next' clashes with reserved keyword.` The `Clocks` section of a
  TimedCGS model follows the same rule.

### Removed

- `ZoneGraph.has_path_from`, `ZoneGraph.find_path_from`,
  `DBMAdapter.compute_predecessors` and the backward path helpers
  `any_backward_path` and `collect_backward_paths` of `trace_utils`. No checker
  called them: TCTL and TOL build the region graph forward.

- Breaking: `read_from_model_object` of CGS, CapCGS and CostCGS (and the
  ObstructionModel stub). Nothing called it, and it skipped the checks of
  `read_file` (no wallets for a WalletCGS, no name checks). Use `read_file`.
- Breaking: WalletCGS `get_valid_actions`, `get_next_states` and
  `simulate_transition`. Wallet_ATL never called them, and they differed from the
  Wallet ATL paper (AAMAS 2026): they exempted the last agent from the wallet
  check (Def. 4.1) and moved balances along transitions (Def. 4.4 does not). Use
  `check_action_feasibility` and `is_profile_feasible`; balances are not updated
  along transitions.
- Breaking: the helpers only the old CTL traces used. In
  `algorithms.explicit.shared`: `reconstruct_trace_from_predecessors`,
  `build_predecessor_map_bfs`, `build_predecessor_map_forward`,
  `extract_shortest_trace`, `least_fixpoint_with_trace`. In
  `algorithms.explicit.CTL`: module `operators_with_trace`,
  `preimage.pre_image_exist_with_trace`, `solver.solve_tree_with_trace`,
  `solver.extract_trace_for_result`. Also the `max_length` parameter of
  `reconstruct_trace_bfs` (the limit is `MAX_TRACE_LENGTH`). `solver.solve_tree`
  labels the tree, and `traces.build_trace` builds the trace with
  `reconstruct_trace_bfs` and `find_lasso`.

## [1.7.0] - 2026-11-05

### Added

- `ATL_STAR.synthesize_strategy(formula, filename, state=None)`, a separate
  entry point returning a JSON-serializable witness strategy
  (`{"satisfied": bool, "strategy": {"start": ..., "moves": [...],
  "transitions": [...]} | None, ...}`), kept out of
  `model_checking` so that one stays focused on plain model checking. Only
  supports a formula whose outermost operator is a single coalition with
  no further coalition nested inside its path formula. Broader formula
  shapes are rejected with a clear "semantic" error, deferred to a later
  iteration. See `docs/ATL_STAR/algorithm.md`.
- `ObstructionModel`, the model type for COTL: a graph whose edges demons
  disable at a cost (sections `Number_of_demons`, `Demon_actions`, `Curses`;
  see `docs/file_formats.md`).
- COTL weak next `WX`, an empty legion `<><n>`, and budget 0.
- OATL accepts `R`, `W`, the parenthesised form `<A><n> (phi U psi)`, and
  budget 0.

### Changed

- **Breaking:** OATL now follows Catta et al., "Obstruction Alternating-time
  Temporal Logic", AAMAS 2024. `<A><n>` means the Demon erases joint actions of
  total cost at most `n` per step so that, whatever `A` does, some remaining
  path satisfies the formula. Earlier versions checked whether `A` had one
  move of cost `<= n` into the target. Recompute OATL results. A missing cost
  that decides the result is now an error instead of 0, and the ATL prefilter
  is dropped.
- **Breaking:** COTL now follows Catta et al., "Coalition Obstruction Temporal
  Logic", IJCAI 2025. `<G><n>` is a legion of demons with budget `n` per step.
  Earlier versions ran a cost-bounded coalition on a `costCGS`. Recompute COTL
  results and convert models to `ObstructionModel`; `costCGS` files are now
  rejected. `R`, `G` and `W` also hold on a path that stops because every edge
  out of its last state is disabled.
- OATL and COTL no longer share parser or pre-image code.
- `spottl` (Spot's Python bindings, Linux only) is now a regular
  dependency instead of living under the `atl_star` extra. `pip install
  vitamin-model-checker` alone is enough for ATL* to work, no
  `[atl_star]` extra needed.

### Fixed

- ATL_STAR's elimination algorithm could generate a fresh marker
  proposition (`__atl_star_elim_N`) that collided with a real proposition
  already declared in the model, silently corrupting the result for that
  edge case. The marker is now checked against the model's declared
  propositions before use.

### Removed

- `shared/oatl_index_preimage.py`.

## [1.6.5] - 2026-09-15

### Fixed

- NatSL formulas with spaces around `:` or between quantifiers (for example
  `E{1}x : (x, 1) F goal`) no longer fail with
  `Invalid quantifier near ' '; expected E{k}x or A{k}x`. The parser now strips
  the quantifier prefix and binding/goal suffix and accepts flexible whitespace
  inside quantifier and binding tokens.

## [1.6.4] - 2026-09-11

### Added

- ATL* model checking (`model_checker/algorithms/explicit/ATL_STAR/`), an
  automata-theoretic checker (reduction to 2-player parity games) rather
  than the coalition pre-image fixpoint every other logic here uses. It is
  needed because ATL* allows a coalition operator to appear anywhere
  inside a path formula, not only at the formula's own root. Runs over
  plain `CGS`, no new game-structure type. Requires
  [Spot](https://spot.lre.epita.fr/) (`pip install spottl` on Linux, or
  conda-forge elsewhere); the rest of VITAMIN works without it, see
  `docs/ATL_STAR/algorithm.md`.
- `model_checker/automata/`, a vendored, logic-agnostic omega-automata and
  parity-game-solving library (wraps Spot) backing ATL*'s reduction. It is
  available to any future logic that needs the same machinery.
- Restricted executable NatSL one-goal checker with ordered bounded strategy
  quantification and shared `space`/`time` semantics.
- Multi-character NatSL strategy variables.
- NatSL semantic regression tests and dedicated CGS fixtures.
- Runnable NatSL examples, including a logistics-robot case study.
- Reproducible NatSL scalability benchmark with curated recorded results.
- NatSL success payloads now include NatATL-style `res` / `initial_state`
  fields alongside `Satisfiability` for backend compatibility.

### Changed

- Mixed bounded NatSL prefixes are evaluated directly instead of being
  decomposed into independent NatATL checks.
- NatSL uses exact action pruning: strategies selecting unavailable actions are
  treated as inadmissible rather than repaired with an implicit idle action.
- NatSL documentation now describes the implemented `E* A*` one-goal fragment
  and its deliberate boundaries.
- Public NatSL algorithm entry is a single `NatSL` entry point
  (`core.model_checking` with `mode="space"|"time"`). The
  `NatSL_Sequential` / `NatSL_Alternated` packages and entry points were removed.

### Fixed

- NatSL runnable examples used a misspelled `Unkown_Transition_by` header that
  broke CGS loading; examples are synced with the correct fixtures.

## [1.6.3] - 2026-08-26

### Fixed

- `detect_model_type_from_content` recognizes ICTL BirelationalMatrix files
  whose Transition cells use only `0` / `R` / `P` / `P,R` (with a `P` or
  `P,R` marker), instead of classifying them as plain CGS.

## [1.6.2] - 2026-08-25

### Added

- Dedicated COTL parser package; CapATL binary Release (greatest fixpoint).
- Per-logic algorithm docs, architecture/structure docs under docs/.
- Stronger unit/integration coverage (WalletCGS, timedCGS, bounded ATL, parsers).

### Changed
- Parser layout standardized across logics; PLY parsetab files renamed per logic.
- Shared boolean AST allow-lists; Release/Weak Until grammar moved to COTL
  (dropped from OATL/RBATL surface).
- Explicit checkers: unified error/loading paths, thread-safe PLY parsing,
  reused loaded models, fail-closed n_agent defaults.

### Fixed
- Semantics: CTL ER duality; ATL compact joint actions; CapATL Pre/F;
  LTL/TCTL/TOL/ICTL/RBATL theory alignment; Wallet_ATL next/feasibility/until;
  OATL multi-resource costs; NatSL Alternated challenges; NatATL coalition
  validation.
- Models: total CGS transitions (no vacuous AX on sinks); CostCGS keys; timedCGS
  invariants/zones/constraints; model_factory header detection; BCGS factory via
  CGS.

## [1.6.0] - 2026-06-24

### Added

- Logics and entry points for ICTL, IATL, TOL, and TCTL (parsers, metadata, and
  model-checking modules).
- CI checks for wheel/sdist builds, `twine check`, and `mkdocs build --strict`.
- TCTL regression fixtures and tests where AF differs from AG and AU differs
  from EU (`tctl_af_regression.txt`, `tctl_au_regression.txt`).

### Changed

- **Packaging:** Runtime dependencies are declared only in `pyproject.toml`.
  Removed twelve unused packages that were not imported by `model_checker`
  (`automata-lib`, `networkx`, `antlr4-python3-runtime`, `requests`, and
  others). Only `ply`, `numpy`, and `pydantic` are required at install time.
- **Python:** Supported versions are Python 3.11 and 3.12 (`requires-python =
  >=3.11`). Black and Ruff `target-version` settings were aligned with this.
- **Metadata:** Added license, Trove classifiers, keywords, and project URLs for
  the PyPI project page.
- **Version reporting:** `model_checker.__version__` reads the installed
  distribution version from package metadata.
- **Error API:** Consolidated error helpers into `create_error_response(type,
  message)`. The per-type wrappers (`create_syntax_error`, `create_semantic_error`,
  `create_model_error`, `create_system_error`, `create_validation_error`) were
  removed from the public API; callers use `create_error_response` directly.
  The `res` / `initial_state` string fields are unchanged for backward
  compatibility with existing consumers.
- **Typing:** Modernised annotations across the codebase to PEP 585/604 style
  (`dict` instead of `Dict`, `X | Y` instead of `Union`, and so on) so `make
  lint` passes under Ruff with `target-version = "py311"`.
- **Documentation:** Clarified NatATL Recall PrefilterATL (ATL parse validation
  only, no satisfiability gate), `Node` state renaming after pruning, and TCTL
  fixpoint definitions in `docs/TCTL/algorithm.md`.

### Fixed

- **TCTL:** `AF` used the same least-fixpoint complement as `AG` instead of
  `All \ EG(not phi)`; corrected to a greatest-fixpoint formulation.
- **TCTL:** `A[phi U psi]` used an existential timed predecessor where a
  universal backward step (`AX`) is required; aligned with the CTL dual
  formulation.
- **TOL:** `ClockExpr` now intersects clock-guard regions with the subject
  formula (matching TCTL region-level behaviour at the location-name layer).
- **TOL:** `FreezeExpr` handler signature aligned with `ClockExpr`; freeze at
  the location-name abstraction remains a no-op when clock reset does not change
  the location.

### Removed

- `setuptools` as a runtime dependency (it remains a build-time requirement
  only).
- Dead NatATLF modules `strategies.py` and `pruning.py` (Recall delegates to
  NatATL Memoryless; these copies were unused and outdated).
