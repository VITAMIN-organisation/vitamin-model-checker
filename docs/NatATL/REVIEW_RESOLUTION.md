# Review resolution: fixes, qualified changes and rejected alternatives

Basis: the uploaded feat/natatl-model-checking ZIP and the supplied review
emails. Main was inspected for snapshot differences; ZIPs do not establish git
ancestry, and no remote repository was modified. Do not replace main with this
feature snapshot. Apply the patch only after a baseline/applicability check.

| Request | Resolution | Principal implementation / test |
|---|---|---|
| Infer action arity from coalition | Accepted as a real bug. Require full-model num_agents and update every current caller. Ignore no-edge sentinels in inventories. | cgs_actions; LTL/strategies; regression partial coalition |
| Keep IDLE for old LTL callers | Rejected as a semantics-changing workaround. Keep exact pruning. Reject inadmissible candidates before CTL, and make false guards no-ops under ordered priority. | LTL/pruning; no-vacuous-AF and false-guard regressions |
| Missing Recall IDLE in some states | Adopted as an explicit supported-input contract for quantified agents, checked before shortcuts. No requirement on unquantified opponents. | RecallContext.require_idle; negation, k=0 and opponent regressions |
| Stop once initial state wins | Implemented only through explicit partial-result mode. Default full-state-set API and nested evaluation remain exact. | return_all_states=False; metadata/early-stop regression |
| Merge equivalent memoryless guards/policies | Deduplicate valid complete policies by exact state-to-action behavior; cost-ordered enumeration preserves cheapest witness. p and p&&q are not equivalent without a model-specific reason. | modal_backend; k=5 instrumentation test |
| Recall repeated parsing and compilation | Shared validated snapshot and run-local caches; reuse rule appropriateness including negative results. | recall_context; one-prepare and cache-hit tests |
| Keep cheapest guard for each Recall meaning | No unsound finite-history quotient added. Existing syntactic normalization and exact caches remain; any future semantic quotient needs exact language equivalence and cost/admissibility preservation. | SEMANTIC_CONTRACT; independent derivative oracle |
| Plain guards fail on G/E/AF | Separate Boolean guard evaluator, shared with history monitors. No mutable model cache, no claim of epistemic-K support. | boolean_guards; three reserved-looking AP tests |
| Changed memoryless fixture | Preserve the old model explicitly with bound-sensitive expectations; retain separate positive cases. Also preserve rejection tests for the old nondeterministic C fixture. | review regressions; NatATL/NatATLF/e2e tests |
| Circular/small regex completeness test | Replace sampled-word equivalence by an independent AST/cost/derivative oracle and exact automaton-product comparison for tested expressions. Exhaustive raw sizes 1..4 plus targeted size-8 prefix-normalization cases, not an impractical unqualified size-8 exhaustive claim. | test_independent_regex_oracle.py |
| Nested assert only checks Boolean type | Replace with independently justified True; add public memoryless opponent X/U and nested tests, negation and distinct witnesses. | recall complete-grammar tests; review regressions |
| Huge printed test and bad paths | Split into focused tests; remove prints; correct pytest/document references. | test_complete_supported_grammar.py |
| Output bound/format drift | Preserve requested bound; separate witness cost; boolean initial-state text; stable set-form res; label partial/undecided states. | both public backends; compatibility tests |
| Model errors classified as system errors | Shared tagged model preflight; propagate unsupported inputs instead of converting to False. | semantic_snapshot; matrix_utils; public wrappers |
| Remove old Recall solver | Retire unsafe height-four entry point with explicit migration error. No fabricated conversion from legacy CTL goals into NatATL. | Recall/solver.py; migration regression |
| Remove memoryless solver / agent_actions | Do not remove: NatATLF still calls it. Preserve and document the compatibility parameter. | NatATLF/NatATL.py; Memoryless/solver.py |
| Remove old Recall helpers | Do not indiscriminately remove: NatSL uses old tree/pruning helpers; states_with_atom remains a small tested utility. | NatSL shared_recall imports; helper test |
| Impossible deadlock / T checks | Eliminate redundant branches where invariants guarantee impossibility; validate seriality at the relevant boundary instead. | modal_backend; lazy_generation |
| Three CGS readers | Share immutable strict snapshot. Retain thin adapters for callers, not duplicate parsers. | semantic_snapshot; Recall wrappers |
| Global appropriateness required for every memoryless rule | Reject as an unconditional assertion: note 3 permits effective first-match guards. Provide explicit global option and a test where equal k gives different answers. | compile_memoryless_profile; global/first-match regression |

## Independent expectations worth reviewing

For the original two-state fixture `[[0, a], [0, I]]` with p true only in the
second state, first-match semantics admits `(p, I); (T, a)` at cost 2. Thus
bound 1 is false and bounds 2 and 3 are true. Replacing the fixture or assuming
that lack of globally available IDLE itself makes it an invalid memoryless CGS
would miss the arbitrary-action fallback and the operational convention.

The existing four-state fixture with the same complete joint action C leading
from s0 to two different successors is not a deterministic CGS. It is retained
as a negative preflight test, not silently rewritten. A separate deterministic
fixture serves the positive NatATLF/e2e cases.

## Verification and limits

The accompanying external test report records exact ZIP hashes, interpreter
and dependency versions, commands, baseline failures and full patched-suite
results. Baseline failures include API and input-contract tests: their number
is not the number of independent soundness bugs. Tests establish reproducible
behavior, not universal soundness or generator completeness.

The local environment used Python 3.13.5 / NumPy 2.3.5 rather than the project's
NumPy 1.26 pin and Python 3.11/3.12 deployment combination. PLY 3.11 came from an
already installed vendored package, and the local project was installed editable
without dependencies for entry-point discovery. No algorithm was replaced by a
mock to obtain the reported suite result. Re-run in a fresh supported Codespace
environment before merging. Existing mocks inside tests remain ordinary test
instrumentation.

Before merge, explicitly approve the semantic contract, inspect the patch and
run CI with the project's dependency pins. General legacy LTL translation,
deviation-enumeration completeness and epistemic support remain outside the
claim of this repair (see SEMANTIC_CONTRACT.md).
