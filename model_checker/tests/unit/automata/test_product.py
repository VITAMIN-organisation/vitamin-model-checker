"""Product of an automaton with a transition system, and complete(), which sends missing moves to a losing sink.

A symbol is the set of propositions true on that step. Needs Spot.
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import (
    AcceptanceCondition,
    AcceptanceKind,
    ParityKind,
    ParityStyle,
)
from model_checker.automata.automaton import Automaton
from model_checker.automata.games.arena import concurrent_to_turnbased
from model_checker.automata.games.game import Game
from model_checker.automata.games.solver import solve
from model_checker.automata.product import complete, product
from model_checker.automata.transition_system import TransitionSystem


def _ts(*edges):
    ts = TransitionSystem()
    for source, symbol, target in edges:
        ts.add_transition(source, symbol, target)
    ts.add_state("s0", initial=True)
    return ts


def _init(automaton):
    return automaton.graph.get_init_state_number()


def test_product_pairs_states_and_reaches_a_fixed_point_on_the_self_loop():
    """`a & F b` on s0 -{a}-> s1 -{a,b}-> s1: one product state at s1 loops on itself."""
    automaton = Automaton(graph=spot.translate("a & Fb", "parity", "deterministic"))
    result, _ = product(
        automaton,
        _ts(("s0", frozenset({"a"}), "s1"), ("s1", frozenset({"a", "b"}), "s1")),
    )
    assert result.initial_states == {("s0", _init(automaton))}
    assert {ts_state for ts_state, _ in result.states} == {"s0", "s1"}
    loops = [
        s
        for s in result.states
        if s[0] == "s1" and result.successors(s, frozenset({"a", "b"})) == {s}
    ]
    assert len(loops) == 1


def test_product_drops_moves_the_automaton_cannot_read():
    """G a has no edge where a is false, so the {} move from s0 disappears."""
    automaton = Automaton(graph=spot.translate("Ga", "parity", "deterministic"))
    result, _ = product(automaton, _ts(("s0", frozenset(), "s1")))
    assert result.successors(("s0", _init(automaton)), frozenset()) == set()


def test_product_reads_a_string_symbol_as_one_proposition():
    """`grant` is one proposition, not the letters g, r, a, n, t."""
    automaton = Automaton(graph=spot.translate("grant", "parity", "deterministic"))
    result, _ = product(automaton, _ts(("s0", "grant", "s1")))
    assert result.successors(("s0", _init(automaton)), "grant") != set()


def test_objective_marks_product_edges_where_the_automaton_marks_its_own():
    """For F b only the loop after b is accepting, not the waiting loop at the start."""
    automaton = Automaton(graph=spot.translate("Fb", "parity", "deterministic"))
    result, objective = product(
        automaton,
        _ts(
            ("s0", frozenset(), "s0"),
            ("s0", frozenset({"b"}), "s1"),
            ("s1", frozenset(), "s1"),
        ),
    )
    start = ("s0", _init(automaton))
    assert objective.priorities
    assert (start, frozenset(), start) not in objective.priorities
    assert all(
        target in result.successors(source, symbol)
        for source, symbol, target in objective.priorities
    )


@pytest.mark.parametrize(
    "objective",
    [
        AcceptanceCondition(
            kind=AcceptanceKind.BUCHI, priorities={(("s0", 0), "a", ("s0", 0)): 0}
        ),
        AcceptanceCondition(kind=AcceptanceKind.CO_BUCHI),
        *(
            AcceptanceCondition(
                kind=AcceptanceKind.PARITY, parity_kind=kind, parity_style=style
            )
            for kind in ParityKind
            for style in ParityStyle
        ),
    ],
    ids=lambda o: f"{o.kind.name}-{o.parity_kind.name if o.parity_kind else ''}-{o.parity_style.name if o.parity_style else ''}",
)
def test_sink_added_by_complete_loses_under_every_objective(objective):
    """b is missing from the product, so complete() adds a sink; looping there must lose for player 0."""
    product_ts = TransitionSystem()
    product_ts.add_transition(("s0", 0), "a", ("s0", 0))
    product_ts.add_state(("s0", 0), initial=True)
    completed, completed_objective = complete(
        product_ts, objective, _ts(("s0", "a", "s0"), ("s0", "b", "s0"))
    )

    [sink] = completed.states - {("s0", 0)}
    assert completed.successors(("s0", 0), "b") == {sink}
    assert completed.successors(sink, "a") == completed.successors(sink, "b") == {sink}
    assert (("s0", 0), "b", sink) not in completed_objective.priorities

    game = Game(
        arena=completed,
        player_states={0: set(completed.states), 1: set()},
        objective=completed_objective,
    )
    assert sink in solve(game).winning_regions[1]


def test_complete_changes_nothing_when_no_move_is_missing():
    """The product already has every move of the system, so no sink and no new priority."""
    product_ts = TransitionSystem()
    product_ts.add_transition(("s0", 0), frozenset(), ("s0", 0))
    product_ts.add_state(("s0", 0), initial=True)
    objective = AcceptanceCondition(
        kind=AcceptanceKind.PARITY,
        parity_kind=ParityKind.MAX,
        parity_style=ParityStyle.ODD,
    )
    completed, completed_objective = complete(
        product_ts, objective, _ts(("s0", frozenset(), "s0"))
    )
    assert completed.states == product_ts.states
    assert completed.transitions == product_ts.transitions
    assert completed_objective.priorities == {}


def test_complete_needs_the_parity_style_to_pick_a_losing_color():
    """Without ODD or EVEN there is no way to know which color rejects."""
    product_ts = TransitionSystem()
    product_ts.add_transition(("s0", 0), frozenset(), ("s0", 0))
    with pytest.raises(ValueError, match="parity_style"):
        complete(
            product_ts,
            AcceptanceCondition(kind=AcceptanceKind.PARITY),
            _ts(("s0", frozenset(), "s0"), ("s0", frozenset({"a"}), "s0")),
        )


def test_completed_next_automaton_can_be_solved():
    """X b has no edge after a step without b, so the plain product deadlocks; complete() makes it solvable."""
    automaton = Automaton.from_ltl("X(b)")
    ts = _ts(("s0", frozenset({"b"}), "s0"), ("s0", frozenset(), "s0"))
    completed, objective = complete(*product(automaton, ts), ts)

    wrapped = TransitionSystem()
    for state in completed.states:
        wrapped.add_state(state, initial=state in completed.initial_states)
    for (source, symbol), targets in completed.transitions.items():
        for target in targets:
            wrapped.add_transition(source, frozenset({("p", symbol)}), target)
    game = concurrent_to_turnbased(wrapped, controlled_players={"p"})
    game.objective = objective
    assert ("s0", _init(automaton)) in solve(game).winning_regions[0]
