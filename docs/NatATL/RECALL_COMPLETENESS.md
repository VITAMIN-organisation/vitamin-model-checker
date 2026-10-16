# NatATL Recall: exhaustiveness for the implemented bounded grammar

**Scope.** The public Recall input contract also requires IDLE in every state
for each agent quantified by a strategic modality (not for unquantified
opponents). Missing IDLE is an explicit unsupported-model error, including
at unreachable states and before semantic shortcut refutations.

The theorem below applies to the implemented finite, *deterministic,
total, rectangular* concurrent game structure (CGS) semantics, with a finite
set `Prop` of valid, nonreserved atomic identifiers. It concerns **only** the
following grammar and significant-pattern cost convention, not every syntactic
choice or model class that might be allowed by other presentations of NatATL.

## Exact language and strategy conventions

The Boolean grammar is

```
b ::= T | false | p | !b | (b && b) | (b || b)    (p in Prop)
```

The regular-history grammar is

```
r ::= b | (r . r) | (r | r) | (r)*
```

Boolean brackets and parentheses are cost-free grouping. `r` matches the
**entire** sequence of valuations along a finite nonempty CGS history,
including initial and current states. Star permits the empty word as usual.
Negation applies **only** to a Boolean letter test, not to an arbitrary regex.
The metric is raw AST node count, except recursively:

- `||T*|| = 1`;
- `||T*.r|| = ||r||` (also after associating concatenation);
- all other syntax counts each atom and operator once.

Alias `true` denotes `T` and redundant parentheses have zero cost. Each agent
uses an **ordered** guarded-action list ending in `(T*, IDLE)`. Every pair is
globally appropriate: when its guard matches any legal history of the original
CGS, its action must be enabled for that agent in the final state. The fallback
is mandatory and contributes cost 1. Strategy cost sums its rule costs; a
coalition's cost sums its member costs. The first matching rule selects the
coalition action; the opponent's actions are unrestricted.

## Completeness theorem (supported grammar)

**Theorem.** Fix a finite CGS in the class above, coalition `A` (nonempty),
complexity bound `k` (finite), initial state `q`, and a strategic objective
`X psi`, `F psi`, `G psi`, `psi U theta`, or `psi W theta`, where `psi` and
`theta` are exact truth sets of CGS states. Assuming the automaton/product and
universal-fixpoint algorithms implement their stated semantics, the extended
search (`collective_full_strategies`) finds an appropriate winning strategy of
total complexity at most `k` **iff** one exists in this declared grammar.
Consequently, complete exhaustion gives the Boolean verdict `False` **within
this grammar**. A nested formula composed using Boolean connectives and these
strategic operators is also two-valued, by structural induction over its AST.

### Proof of enumeration completeness

1. **Boolean expressions.** Induction on raw size `n`: at `n=1`, enumerate
   `T`, `false`, and every proposition. For `!b`, recurse at `n-1`; for either
   binary connective, partition `n-1` into every pair of positive child sizes.
   Thus every Boolean AST has a representative at its exact raw cost.
2. **Raw regular expressions.** Induction on raw size `n`: Boolean tests are
   enumerated as above. Star recurses at `n-1`. Concatenation and union recurse
   over every positive partition of `n-1`. All constructors are parenthesized
   by the renderer, avoiding precedence ambiguity. `T*` is represented by
   canonical spelling even when generated from `(T)*`.
3. **Significant-cost normal form.** Flatten only *outer* concatenation using
   associativity (never cross a union or enter a Kleene star). Remove all
   consecutive initial factors `T*`: `T* . T*` has the same regular language as
   `T*`, and concatenating `T*` to itself does not change the prefix language.
   - If nothing remains, use `T*` of cost 1.
   - If a suffix `s` remains, it has no initial top-level `T*` factor and its
     **raw** cost is exactly the normalized significant cost of the original
     regex. The generator enumerates `s` at that raw size and emits `T*.s`
     at that significant cost.
   - If the original regex had no initial `T*`, its significant cost equals
     its raw cost; the raw-size generator emits it unchanged.
   This also covers arbitrarily many repeated free prefixes at fixed cost.
   The `_has_free_prefix` filter only removes unnormalized raw expressions
   already represented by the canonical free-prefix case.
4. **Ordered strategies.** Replace each rule guard with its equivalent normal
   form without increasing cost; this preserves matching on *all histories*,
   global rule appropriateness, and chosen actions. If identical guards occur
   more than once in the non-fallback prefix, only the first can be selected;
   remove later prefix duplicates. Never remove the mandatory final `(T*, IDLE)`
   rule, even when an earlier `T*` rule shadows it: it still contributes cost 1.
   Every remaining guard costs at least 1, hence there are finitely many rules
   at bound `k`. `individual_full_exact_cost` enumerates every ordered list,
   action assignment, and positive rule-cost partition ending in the mandatory
   fallback. If normalization removes rules, the resulting profile still has
   cost at most `k` and is enumerated at its new cost.
5. **Coalitions.** `collective_full_strategies` visits all positive partitions
   of each total cost from `|A|` to `k` among coalition agents and enumerates
   their individual strategies, covering every normalized collective profile.
6. **Semantics of a fixed profile.** Global appropriateness is decided by
   finite reachability in CGS x guard automata from every state. The reachable
   strategy product fixes coalition actions while keeping all adversarial
   responses. Since the CGS is deterministic, total, and rectangular, every
   selected legal joint profile has exactly one successor and the product is
   total. Finite least/greatest universal fixpoints decide `X,F,G,U,W` exactly,
   regardless of path length. Any unexpected validation/product error is
   propagated; it is never mistaken for an inadmissible candidate or `False`.

By (1)–(6), searching and checking each generated profile yields a witness iff
one exists in the declared grammar; after a *completed* search, `False` is
correct. For nested modal ASTs, atomic and Boolean nodes are two-valued and
each inner modality is decided at every original CGS state before the parent
modality evaluates its operands. Negation therefore complements exact truth
sets rather than approximations.

## Software flags and limitations

- Public `NatATL/Recall/natatl_recall.py` uses the **extended** generator and
  enables `complete_supported_grammar=True`. It returns definitive
  `Satisfiability` `True` or `False` for a successfully completed check on a
  valid CGS **within the supported grammar**.
- Direct callers of `solve_bounded_recall()` remain conservative by default.
  `certify_restricted_exhaustion=True` is only legal with `generator="extended"`.
  `generator="canonical"` remains an incomplete subset and cannot use the
  certification flag.
- `Supported Grammar Complete=True` is deliberately distinct from
  `Full Language Complete=False`: no claim is made for primitive regex
  complement/epsilon, alternative operator-cost conventions, missing/wildcard
  joint profiles, nondeterministic transitions, or unsupported grammar
  extensions. The public text parser currently exposes `X,F,G,U`; `W` is
  supported at the evaluator AST/backend level, pending text-parser support.
- Exhaustive generation is combinatorial and may be computationally
  prohibitive at high bounds. There is no unsound iteration or history-depth
  cap. An **interrupted** run or exception is never a completed exhaustive
  negative verdict.
- The proof is a mathematical structural argument, **not** a machine-checked
  formalization in Lean. Unit tests, bounded regex-language equivalence, and
  independent semantic examples corroborate but do not replace that proof.


## Review regression methodology

`test_independent_regex_oracle.py` constructs its own Boolean/regex ASTs and cost
function. It exhausts raw ASTs through size 4, and has explicit raw-size 8
free-prefix cases. A Brzozowski-derivative/NFA product checks language equality
on **all** finite words over the test alphabet, not only words of bounded length.
This finite set of checked ASTs is still a test suite, not a proof for arbitrary k.
Caches use the fixed model snapshot; no sampled-history equivalence is used to
prune production Recall guards.
