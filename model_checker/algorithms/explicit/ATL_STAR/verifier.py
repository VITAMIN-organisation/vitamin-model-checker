"""ATL* model checking with automata and parity games.

- A coalition nested in a path formula is first replaced by a new proposition, so
  the rest is plain LTL for `Automaton.from_ltl`.
- The game is solved from every CGS state at once, because a verdict is needed for
  each state, not only the initial one.
"""

from __future__ import annotations

import itertools
from collections.abc import Hashable, Iterator
from dataclasses import dataclass, field, replace
from typing import cast

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
    """A coalition's winning strategy and the position to start it from.

    Positions pair a CGS state with an automaton state, which remembers how far the
    formula has got; read nested witnesses through `nested_witnesses_at`.
    """

    strategy: Strategy
    start: tuple[str, int]
    product_ts: TransitionSystem
    nested: dict[str, dict[str, Witness]] = field(default_factory=dict)

    def nested_witnesses_at(self, state: str) -> list[Witness]:
        """The nested coalitions' witnesses that apply at `state` (usually 0 or 1)."""
        return [
            by_state[state] for by_state in self.nested.values() if state in by_state
        ]

    def advance(self, symbol: Hashable) -> Witness | None:
        """The witness after one step with the joint action `symbol`, or None if the
        step leads nowhere. Switches to a nested witness when the new state has one.

        Raises ValueError if the step is ambiguous (several successors or nested
        witnesses).
        """
        targets = self.product_ts.successors(self.start, symbol)
        if not targets:
            return None
        if len(targets) > 1:
            raise ValueError(
                f"{symbol!r} from {self.start!r} has {len(targets)} possible successors, not 1"
            )
        (next_state,) = targets
        if not isinstance(next_state, tuple):
            return None  # complete()'s rejecting sink: the path formula fails here
        nested_here = self.nested_witnesses_at(next_state[0])
        if len(nested_here) > 1:
            raise ValueError(
                f"{next_state[0]!r} has {len(nested_here)} nested witnesses available at once"
            )
        if nested_here:
            return nested_here[0]
        return replace(self, start=next_state)


@dataclass(frozen=True)
class _CoalitionSolution:
    """What `_sat_coalition` and `witness` read from solving one coalition's game."""

    winning: set[Hashable]
    strategy: Strategy
    aut_init: int
    product_ts: TransitionSystem
    nested: dict[str, dict[str, Witness]]


def sat(formula: Formula, model: AdaptedCGS) -> set[str]:
    """The states of `model` where `formula` holds; ValueError if it is not a state
    formula or names an unknown proposition."""
    if isinstance(formula, Prop):
        if formula.name not in model.propositions:
            raise ValueError(
                f"{formula.name!r} is not among the model's declared "
                f"propositions {sorted(model.propositions)}"
            )
        return {state for state, props in model.labels.items() if formula.name in props}
    if isinstance(formula, True_):
        return set(model.states)
    if isinstance(formula, Not):
        return set(model.states) - sat(formula.operand, model)
    if isinstance(formula, And):
        return sat(formula.left, model) & sat(formula.right, model)
    if isinstance(formula, Coalition):
        return _sat_coalition(formula, model)
    raise ValueError(
        f"a bare {type(formula).__name__} is not a state formula; "
        "temporal operators need a <<...>> coalition around them"
    )


def holds(formula: Formula, model: AdaptedCGS, state: str | None = None) -> bool:
    """Whether `formula` holds at `state` (default: the initial state)."""
    state = resolve_state(model, state)
    return state in sat(formula, model)


def check(cgs: CGSProtocol, formula_text: str, state: str | None = None) -> bool:
    """Parse `formula_text` and check it on `cgs` at `state` (default: the initial
    state). For several formulas, call `adapt` once and `holds` for each."""
    model = adapt(cgs)
    formula = parse(formula_text, num_agents=len(model.players))
    return holds(formula, model, state=state)


def require_simple_coalition(formula: Formula) -> Coalition:
    """Return `formula` if it is one coalition with no coalition inside, else raise
    ValueError: `synthesize_strategy` can build only one strategy."""
    if not isinstance(formula, Coalition):
        # ValueError, not TypeError: ATL_STAR.py catches only ValueError.
        raise ValueError(  # noqa: TRY004
            "only a formula whose outermost operator is a single coalition "
            "(<<...>> ...) is supported"
        )
    if _contains_coalition(formula.path_formula):
        raise ValueError(
            "a coalition nested inside another's path formula is not supported yet"
        )
    return formula


def _contains_coalition(formula: Formula) -> bool:
    """Whether `formula` has a `Coalition` anywhere inside it (itself included)."""
    if isinstance(formula, Coalition):
        return True
    if isinstance(formula, (Not, Next)):
        return _contains_coalition(formula.operand)
    if isinstance(formula, (And, Until)):
        return _contains_coalition(formula.left) or _contains_coalition(formula.right)
    return False


def witness(
    formula: Coalition, model: AdaptedCGS, state: str | None = None
) -> Witness | None:
    """The coalition's winning strategy for `formula` at `state` (default: the
    initial state), or None if `formula` does not hold there."""
    state = resolve_state(model, state)
    solution = _solve_coalition(formula, model)
    start = (state, solution.aut_init)
    if start not in solution.winning:
        return None
    return Witness(
        strategy=solution.strategy,
        start=start,
        product_ts=solution.product_ts,
        nested=solution.nested,
    )


def resolve_state(model: AdaptedCGS, state: str | None) -> str:
    """`state`, or the initial state when it is None; ValueError if it is unknown."""
    if state is None:
        return model.initial_state
    if state not in model.states:
        raise ValueError(f"{state!r} is not a state of this model")
    return state


def _sat_coalition(formula: Coalition, model: AdaptedCGS) -> set[str]:
    return _truth_set(_solve_coalition(formula, model), model.states)


def _truth_set(solution: _CoalitionSolution, states: frozenset[str]) -> set[str]:
    return {state for state in states if (state, solution.aut_init) in solution.winning}


def _solve_coalition(formula: Coalition, model: AdaptedCGS) -> _CoalitionSolution:
    agents = set(formula.agents)
    if not agents.issubset(model.players):
        raise ValueError(
            f"Coalition agents {sorted(agents)} include ids that aren't among "
            f"the model's players {list(model.players)}"
        )

    nested: dict[str, dict[str, Witness]] = {}
    ltl_formula, labels = _eliminate(
        formula.path_formula, model, dict(model.labels), itertools.count(), nested
    )
    automaton = Automaton.from_ltl(_render_ltl(ltl_formula))

    # Every state starts the product, so `_truth_set` finds each `(state, aut_init)`.
    probe = replace(model.transition_system, initial_states=set(model.states))
    product_ts, objective = product(
        automaton, probe, label=lambda source, _symbol: labels[cast(str, source)]
    )
    product_ts, objective = complete(product_ts, objective, probe)

    game = concurrent_to_turnbased(product_ts, controlled_players=agents)
    game.objective = replace(
        objective, priorities=remap_priorities(objective.priorities, agents)
    )

    solution = solve(game)
    aut_init = automaton.graph.get_init_state_number()
    return _CoalitionSolution(
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
    """Replace each coalition in `psi` with a new proposition, giving plain LTL and
    the labels of the new propositions. Their witnesses are added to `nested`."""
    if isinstance(psi, Prop):
        if psi.name not in model.propositions:
            raise ValueError(
                f"{psi.name!r} is not among the model's declared "
                f"propositions {sorted(model.propositions)}"
            )
        return psi, labels
    if isinstance(psi, True_):
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
        satisfying = _truth_set(inner_solution, model.states)
        name = f"{_FRESH_PROP_PREFIX}{next(counter)}"
        while name in model.propositions:
            name = f"{_FRESH_PROP_PREFIX}{next(counter)}"
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
    """Write a coalition-free `formula` as Spot LTL text."""
    if isinstance(formula, Prop):
        return f'"{formula.name}"'
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
    raise ValueError(
        f"{formula!r} is not pure LTL, elimination should have removed every Coalition"
    )
