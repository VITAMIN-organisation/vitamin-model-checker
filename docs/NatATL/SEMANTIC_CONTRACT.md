# NatATL semantic contract after the review fixes

This document describes the chosen implementation contract. It is not a
mechanized soundness/completeness proof, and the test suite is not such a proof.
The reference is *Natural Strategic Ability*, Sections 4.1 and 6.1. Where that
paper presents alternatives, this document names the alternative rather than
silently treating them as equivalent under the same complexity bound.

## Models and action profiles

The current public NatATL backends require a finite deterministic CGS. In every
state, the table must contain exactly one successor for each combination of the
individual enabled actions. Enabled action sets are inferred from the complete
joint-action table; the format does not have a separate authoritative protocol
function. Repeated occurrences of the same joint action with different targets,
missing Cartesian combinations, malformed arity, nonbinary labels and empty
rows are model errors, not negative answers to a formula. No transitions are
invented. Strict NatATL does not expand wildcard cells. Legacy LTL wildcard
handling remains confined to its own adapter.

Joint-action arity comes from the whole CGS, never from the coalition. For two
agents, compact `AC` denotes `(A, C)` even if the coalition is only agent 1.
Nominal joint actions use the established delimiter syntax. Action extraction
requires the explicit keyword `num_agents`.

## Memoryless strategies

Each strategy is a finite ordered list ending in an explicit `(T, action)`
rule. The fallback action is not necessarily IDLE. Evaluation selects the first
matching rule; the selected action must be enabled in the original CGS.

There are two explicit appropriateness modes:

* `first-match` (default): rule i must be enabled on the states satisfying its
  guard and none of the earlier guards. This is the operational alternative in
  footnote 3 of Section 4.1 of the reference paper.
* `global`: each rule must be enabled at every state satisfying its own guard,
  including states where an earlier rule shadows it. This follows the stronger
  definition in the main text of Section 4.1.

The modes need not yield the same answer at the same bound. Replacing a guard
by its effective first-match condition can increase its syntactic cost. The
result includes `Appropriateness`. Both modes still select actions first-match;
only the admissibility requirement changes. This is not a claim that the two
bounded logics are interchangeable.

Guards are propositional Boolean expressions, interpreted against the labels of
the fixed original model. They are not run through the CTL lexer. In particular,
propositions such as `G`, `E` and `AF` work as guard atoms. Boolean constants are
reserved by the grammar. This evaluator does not implement epistemic K guards.

Pruning retains exactly complete joint actions agreeing with every coalition
member's selected action. Every opponent choice remains. IDLE is retained only
where selected, not as an extra alternative to a selected non-IDLE action.
Validation covers all model states, not only states reached by a winning play.

## Complexity and compositional truth

Memoryless cost is the sum of all guard-symbol counts, excluding parentheses;
the final T costs one. Collective cost is the sum of the individual costs.
Recall uses the significant-pattern metric of Section 6.1; the mandatory T*
fallback also costs one. Bound means strategy cost, never path length or number
of attempted candidates.

Nested modalities are evaluated in the original game using their own strategy
quantifiers, coalitions and bounds. Negation and Boolean connectives operate on
those state truth sets. A single strategy is not reused to witness independent
existential modalities.

`Complexity Bound` retains the bound requested by the top-level modality;
`Witness Complexity` is separate and appears when a witness is available.
The default memoryless result is a complete state set. The explicit
`return_all_states=False` option can stop the top-level strategic search after
deciding the initial state. Nested operands are still evaluated exactly. A
partial result is marked `State Set Complete: False` and has queried-state
fields, not a purported full `Satisfying States` list.

## Recall

The current Recall implementation adopts global guarded-action appropriateness
and the mandatory `(T*, IDLE)` fallback from Section 6.1. Its supported-input
contract therefore requires IDLE in every model state for every agent
quantified by a modality, including unreachable states. This is checked before
bound or reachability shortcuts. An opponent that is never quantified need not
have IDLE. An unsupported model raises a model error; it is not reported as an
exhaustive strategic failure and then turned into a positive answer by negation.
This is an explicit domain restriction of this implementation, not a claim that
all possible NatATL formulations must reject every such CGS.

The model is parsed and validated once per checking run. Immutable snapshots,
compiled regex monitors, and positive/negative global-rule appropriateness
results are reused locally. Cached results are never attached to a mutable CGS
or shared across unrelated runs/models. A rule cache keyed by guard alone would
not justify prefix-independent first-match appropriateness; that is not what
this Recall cache claims.

A finite product of CGS states and regular-history monitor states represents the
outcomes of each fixed candidate. Universal temporal fixpoints operate on the
resulting total finite graph. This is not a fixed-depth unrolling. The obsolete
height-four Recall solver raises an explicit migration error if called; the
public Recall entry point uses the automata product. Other old Recall utilities
remain because NatSL or tests still import them.

Complete negative answers apply only to the explicitly supported grammar and
cost metric documented in `RECALL_COMPLETENESS.md`. An incomplete search mode
must preserve undecided states. This patch does not claim a mechanically
verified proof of that grammar's enumeration theorem or support for all regular
expression extensions.

## Optimizations and their conditions

Memoryless policies are deduplicated only after admissibility validation, by
the exact selected coalition actions at every model state. Cost-ordered search
retains a cheapest representative. Equivalent-looking text is not enough:
`p` and `p && q` are interchangeable only when their denotations agree on the
fixed model for this use.

Recall compilation and appropriateness are cached without quotienting regex
languages from bounded sample words. Equal results on short histories do not
establish language equivalence. A future language-based optimization must use
an exact equivalence relation and preserve appropriateness, cost and the
mandatory fallback. No finite-sample equivalence is used in production here.

## Legacy LTL and solution concepts: deliberately limited scope

The shared-component repairs pass full arity, respect ordered rules, reject
nonserial pruned candidates before CTL, and reject inadmissible supplied profiles
before Nash payoff tests. Legacy generated lists may omit a fallback: their
adapter selects existing IDLE only at uncovered states. It does not invent
IDLE edges. Constant `(T, action)` candidates are included so that valid
constant policies are not lost after invalid partial policies are rejected.

These changes do NOT certify the general legacy LTL/SolutionConcepts pipeline.
In particular, the old syntactic temporal-prefix converter is not a general
LTL-to-CTL translation; A(F p or F q) need not equal AF p or AF q on a branching
outcome structure. The completeness of the legacy strategy/deviation generator,
individual objective assignments, and epistemic uniformity are separate proof
and implementation obligations. This review patch neither removes those
limitations silently nor purports to implement the complete iCGS paper.

## Errors and compatibility

Malformed models are errors. Inadmissible generated candidates are skipped.
Unsupported syntax/backend failures are errors, not false guards or losing
strategies. Inconclusive incomplete searches are not verified negatives.

The `num_agents` extraction keyword is now mandatory: external callers must be
updated. The retired legacy Recall solver is a fail-closed migration boundary,
not an unnoticed API deletion. Memoryless legacy solver arguments remain for
NatATLF compatibility. The stricter deterministic-CGS preflight is an
intentional input-contract tightening, documented and tested separately from
positive fixtures.
