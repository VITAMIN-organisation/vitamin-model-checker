"""Bottom-up elimination algorithm for ATL* model checking, built on
automata's Automaton/product/arena/solver pipeline.

`sat(formula, model)` computes formula bottom-up on the AST. The only
non-trivial case is `Coalition(agents, psi)`: `psi` may itself contain
nested `Coalition` subformulas, so `_eliminate` first replaces every
maximal one with a fresh proposition labelling the states where it already
holds (via `_solve_coalition`, which also records that inner coalition's
witness into `Witness.nested`, see `witness` below) — what's left is pure
LTL, translatable via `Automaton.from_ltl`. The automaton is producted
with the CGS, unfolded into a turn-based arena for `agents` vs. everyone
else, and solved as a parity/Büchi/co-Büchi game; `Coalition`'s truth set
is player 0's winning region projected onto the automaton's initial state.

`_sat_coalition` needs a verdict for every CGS state, not just the model's
declared initial one, so it probes the product from every state at once —
`solve()`/`product()`/`complete()` already support that (multiple initial
states, and a possibly-partial `Automaton.from_ltl` transition function).
"""

from __future__ import annotations

import itertools
from collections.abc import Hashable, Iterator
from dataclasses import dataclass, field, replace

from model_checker.automata import (
    Automaton,
    Strategy,
    TransitionSystem,
    complete,
    concurrent_to_turnbased,
    product,
    remap_priorities,
    solve,
)
from model_checker.parsers.formulas.ATL_STAR.formula import (
    And,
    Coalition,
    Formula,
    Next,
    Not,
    Prop,
    True_,
    Until,
)
from model_checker.parsers.formulas.ATL_STAR.grammar import parse
from model_checker.parsers.game_structures.cgs.protocols import CGSProtocol

from .cgs_adapter import AdaptedCGS, adapt

_FRESH_PROP_PREFIX = "__atl_star_elim_"


@dataclass(frozen=True)
class Witness:
    """A synthesized joint strategy for a `Coalition` formula, plus where to
    start reading it.

    `strategy` is a Mealy machine keyed by `(cgs_state, automaton_state)`
    pairs, not bare CGS states — the automaton state is the memory needed to
    resolve the formula's temporal structure (e.g. whether an `U`'s left side
    already held). `start` is that pair at the state `witness()` was asked
    about; `strategy.move(start)` gives the coalition's first joint move.
    `formula.agents` own that move jointly — split it onto one agent's own
    action via `Strategy.project`.

    `nested` carries, for every `Coalition` subformula eliminated out of
    `formula`'s path formula (allowed anywhere, arbitrarily deep, in ATL*),
    that inner coalition's own witness — keyed first by its internal marker
    name (meaningless on its own), then by the CGS state it applies from.
    Most formulas have none; look it up via `nested_witnesses_at` rather than
    the marker names directly. Each inner `Witness` carries its own `nested`
    too, so nesting composes without special-casing depth.

    `product_ts` is the underlying product transition system `advance` walks,
    rarely touched directly.
    """

    strategy: Strategy
    start: tuple[str, int]
    product_ts: TransitionSystem
    nested: dict[str, dict[str, Witness]] = field(default_factory=dict)

    def nested_witnesses_at(self, state: str) -> list[Witness]:
        """Every nested coalition's own witness that applies once a run
        following `strategy` reaches `state` (usually zero or one)."""
        return [by_state[state] for by_state in self.nested.values() if state in by_state]

    def advance(self, symbol: Hashable) -> Witness | None:
        """Follow this witness one real step under `symbol` — the full joint
        action that occurred (this witness's coalition part plus whatever the
        environment played), not just the coalition's own move — returning the
        `Witness` to continue with from wherever that leads.

        Automatically switches to a nested coalition's own witness once the
        resulting state has one available (`nested_witnesses_at`): useful for
        replaying a complete run through an eliminated subformula's ability being
        exercised, not just reached — not required by the formula's own semantics,
        only for demonstrating one.

        Returns:
            `None` if `symbol` has no successor from `start` in the underlying
            product (an unrecognized action, or `complete`'s rejecting sink).

        Raises:
            ValueError: `symbol` has more than one possible successor, or the
                resulting state has more than one nested witness available at
                once — neither decidable from the state alone.
        """
        targets = self.product_ts.successors(self.start, symbol)
        if not targets:
            return None
        if len(targets) > 1:
            raise ValueError(f"{symbol!r} from {self.start!r} has {len(targets)} possible successors, not 1")
        (next_state,) = targets
        if not isinstance(next_state, tuple):
            return None  # complete()'s rejecting sink: this path formula can't be satisfied from here
        nested_here = self.nested_witnesses_at(next_state[0])
        if len(nested_here) > 1:
            raise ValueError(f"{next_state[0]!r} has {len(nested_here)} nested witnesses available at once")
        if nested_here:
            return nested_here[0]
        return replace(self, start=next_state)


@dataclass(frozen=True)
class _CoalitionSolution:
    """What `_sat_coalition` and `witness` both need from solving one
    `Coalition`'s underlying game, computed once, read by each."""

    real_states: set[tuple[str, int]]
    winning: set[tuple[str, int]]
    strategy: Strategy
    aut_init: int
    product_ts: TransitionSystem
    nested: dict[str, dict[str, Witness]]


def sat(formula: Formula, model: AdaptedCGS) -> set[str]:
    """The set of `model` states where the state formula `formula` holds.

    Raises:
        ValueError: `formula` isn't a state formula (a bare `Next`/`Until`
            outside a `Coalition`'s path formula).
    """
    if isinstance(formula, Prop):
        return {state for state, props in model.labels.items() if formula.name in props}
    if isinstance(formula, True_):
        return set(model.transition_system.states)
    if isinstance(formula, Not):
        return set(model.transition_system.states) - sat(formula.operand, model)
    if isinstance(formula, And):
        return sat(formula.left, model) & sat(formula.right, model)
    if isinstance(formula, Coalition):
        return _sat_coalition(formula, model)
    raise ValueError(f"{formula!r} is not a state formula")


def holds(formula: Formula, model: AdaptedCGS, state: str | None = None) -> bool:
    """Whether `formula` holds at `state` (default: `model`'s own initial state).

    Raises:
        ValueError: `state` isn't a state of `model`.
    """
    state = _resolve_state(model, state)
    return state in sat(formula, model)


def check(cgs: CGSProtocol, formula_text: str, state: str | None = None) -> bool:
    """Parse `formula_text` and check it against `cgs` at `state` (default: `cgs`'s own initial state).

    Convenience wrapper composing `parser.parse`, `cgs_adapter.adapt`, and
    `holds`, call them separately instead when checking several formulas
    against the same CGS, to adapt it only once.

    Raises:
        ATLStarParseError: `formula_text` is malformed, or a coalition names
            an agent id outside `cgs`'s own agents.
        ValueError: the parsed formula isn't a state formula.
    """
    model = adapt(cgs)
    formula = parse(formula_text, num_agents=len(model.players))
    return holds(formula, model, state=state)


def witness(formula: Coalition, model: AdaptedCGS, state: str | None = None) -> Witness | None:
    """The coalition's own witness strategy for `formula` at `state`
    (default: `model`'s own initial state), or `None` if `formula` doesn't
    hold there.

    Raises:
        ValueError: `state` isn't a state of `model`, or an agent in
            `formula.agents` isn't among `model.players`.
    """
    state = _resolve_state(model, state)
    solution = _solve_coalition(formula, model)
    start = (state, solution.aut_init)
    if start not in solution.winning:
        return None
    return Witness(strategy=solution.strategy, start=start, product_ts=solution.product_ts, nested=solution.nested)


def _resolve_state(model: AdaptedCGS, state: str | None) -> str:
    if state is None:
        (state,) = model.transition_system.initial_states
        return state
    if state not in model.transition_system.states:
        raise ValueError(f"{state!r} is not a state of this model")
    return state


def _sat_coalition(formula: Coalition, model: AdaptedCGS) -> set[str]:
    return _truth_set(_solve_coalition(formula, model))


def _truth_set(solution: _CoalitionSolution) -> set[str]:
    return {
        cgs_state
        for cgs_state, aut_state in solution.real_states
        if aut_state == solution.aut_init and (cgs_state, aut_state) in solution.winning
    }


def _solve_coalition(formula: Coalition, model: AdaptedCGS) -> _CoalitionSolution:
    agents = set(formula.agents)
    if not agents.issubset(model.players):
        raise ValueError(
            f"Coalition agents {sorted(agents)} include ids that aren't among "
            f"the model's players {list(model.players)}"
        )

    nested: dict[str, dict[str, Witness]] = {}
    ltl_formula, labels = _eliminate(formula.path_formula, model, dict(model.labels), itertools.count(), nested)
    automaton = Automaton.from_ltl(_render_ltl(ltl_formula))

    probe = replace(model.transition_system, initial_states=set(model.transition_system.states))
    product_ts, objective = product(automaton, probe, label=lambda source, symbol: labels[source])
    real_states = set(product_ts.states)
    product_ts, priorities = complete(product_ts, objective.priorities, probe)

    game = concurrent_to_turnbased(product_ts, controlled_players=agents)
    game.objective = replace(objective, priorities=remap_priorities(priorities, agents))

    solution = solve(game)
    aut_init = automaton.graph.get_init_state_number()
    return _CoalitionSolution(
        real_states=real_states,
        winning=solution.winning_regions[0],
        strategy=solution.strategies[0],
        aut_init=aut_init,
        product_ts=product_ts,
        nested=nested,
    )


def _eliminate(
    psi: Formula,
    model: AdaptedCGS,
    labels: dict[str, frozenset[str]],
    counter: Iterator[int],
    nested: dict[str, dict[str, Witness]],
) -> tuple[Formula, dict[str, frozenset[str]]]:
    """Replace every maximal `Coalition` subformula in `psi` with a fresh
    proposition, returning the resulting pure-LTL formula and `labels`
    extended with each fresh proposition's truth set. Each eliminated
    `Coalition`'s own witness strategy is recorded into `nested` (mutated in
    place), keyed by the fresh proposition's name then by CGS state, solving
    it already computes one (every solver returns a region and a strategy
    together), so keeping it costs nothing extra."""
    if isinstance(psi, (Prop, True_)):
        return psi, labels
    if isinstance(psi, Not):
        operand, labels = _eliminate(psi.operand, model, labels, counter, nested)
        return Not(operand), labels
    if isinstance(psi, Next):
        operand, labels = _eliminate(psi.operand, model, labels, counter, nested)
        return Next(operand), labels
    if isinstance(psi, And):
        left, labels = _eliminate(psi.left, model, labels, counter, nested)
        right, labels = _eliminate(psi.right, model, labels, counter, nested)
        return And(left, right), labels
    if isinstance(psi, Until):
        left, labels = _eliminate(psi.left, model, labels, counter, nested)
        right, labels = _eliminate(psi.right, model, labels, counter, nested)
        return Until(left, right), labels
    if isinstance(psi, Coalition):
        inner_solution = _solve_coalition(psi, model)
        satisfying = _truth_set(inner_solution)
        name = f"{_FRESH_PROP_PREFIX}{next(counter)}"
        # A bulk dict copy plus updating only `satisfying` (typically much
        # smaller than the full state count) is cheaper at CGS scale than a
        # comprehension that re-touches every state to add a name to a few.
        extended = dict(labels)
        for state in satisfying:
            extended[state] = extended[state] | {name}
        nested[name] = {
            cgs_state: Witness(
                strategy=inner_solution.strategy,
                start=(cgs_state, inner_solution.aut_init),
                product_ts=inner_solution.product_ts,
                nested=inner_solution.nested,
            )
            for cgs_state in satisfying
        }
        return Prop(name), extended
    raise ValueError(f"{psi!r} is not a valid path formula")


def _render_ltl(formula: Formula) -> str:
    """Render a pure-LTL `Formula` (no `Coalition` left) as Spot LTL text.

    Raises:
        ValueError: `formula` still contains a `Coalition` (an `_eliminate` bug).
    """
    if isinstance(formula, Prop):
        return formula.name
    if isinstance(formula, True_):
        return "1"
    if isinstance(formula, Not):
        return f"!({_render_ltl(formula.operand)})"
    if isinstance(formula, Next):
        return f"X({_render_ltl(formula.operand)})"
    if isinstance(formula, And):
        return f"({_render_ltl(formula.left)}) & ({_render_ltl(formula.right)})"
    if isinstance(formula, Until):
        return f"({_render_ltl(formula.left)}) U ({_render_ltl(formula.right)})"
    raise ValueError(f"{formula!r} is not pure LTL, elimination should have removed every Coalition")
