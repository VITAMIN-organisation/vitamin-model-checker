"""Tests for games/solver.py, the Spot-backed game adapter.
Requires Spot, see tests/test_automaton.py. Skipped entirely if spot
isn't importable."""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import (
    AcceptanceCondition,
    AcceptanceKind,
    ParityKind,
    ParityStyle,
)
from model_checker.automata.games.game import Game
from model_checker.automata.games.solver import solve
from model_checker.automata.transition_system import TransitionSystem


def _buchi_objective(*accepting_transitions):
    return AcceptanceCondition(
        kind=AcceptanceKind.BUCHI,
        priorities=dict.fromkeys(accepting_transitions, 0),
    )


def _co_buchi_objective(*marked_transitions):
    return AcceptanceCondition(
        kind=AcceptanceKind.CO_BUCHI,
        priorities=dict.fromkeys(marked_transitions, 0),
    )


def test_player0_wins_when_only_edge_leads_to_accepting_loop():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "loop")
    ts.add_transition("loop", "b", "loop")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0", "loop"}, 1: set()},
        objective=_buchi_objective(("loop", "b", "loop")),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"s0", "loop"}
    assert solution.winning_regions[1] == set()
    assert solution.strategies[0].move("s0") == "a"


def test_opponent_avoids_accepting_loop_when_it_owns_the_choice():
    ts = TransitionSystem()
    ts.add_transition("s0", "escape", "target")
    ts.add_transition("s0", "stall", "dead_end")
    ts.add_transition("target", "loop", "target")
    ts.add_transition("dead_end", "loop", "dead_end")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"target", "dead_end"}, 1: {"s0"}},
        objective=_buchi_objective(("target", "loop", "target")),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"target"}
    assert solution.winning_regions[1] == {"s0", "dead_end"}
    assert solution.strategies[1].move("s0") == "stall"


def test_parity_min_even_accepts_when_minimum_recurring_priority_is_even():
    # s0 -(prio 0)-> s1 -(prio 1)-> s0: min priority seen infinitely often is
    # 0 (even) -> accepting under min-even, forced (no real choice) so p0 wins.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s1", "b", "s0")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0", "s1"}, 1: set()},
        objective=AcceptanceCondition(
            kind=AcceptanceKind.PARITY,
            parity_kind=ParityKind.MIN,
            parity_style=ParityStyle.EVEN,
            priorities={("s0", "a", "s1"): 0, ("s1", "b", "s0"): 1},
        ),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"s0", "s1"}
    assert solution.winning_regions[1] == set()


def test_player0_wins_when_marked_transition_occurs_only_finitely_often():
    # co-Büchi: accepting iff the marked color recurs only finitely often.
    # Forced play (no real choice): s0 ->(marked)-> s1 ->(unmarked)-> s1 ...
    # visits the marked transition exactly once, so player 0 wins.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s1", "b", "s1")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0", "s1"}, 1: set()},
        objective=_co_buchi_objective(("s0", "a", "s1")),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"s0", "s1"}
    assert solution.winning_regions[1] == set()


def test_player0_loses_when_marked_transition_recurs_infinitely_often():
    # forced self-loop on the marked transition: visited infinitely often,
    # so co-Büchi rejects and player 0 (the only owner) loses everywhere.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0"}, 1: set()},
        objective=_co_buchi_objective(("s0", "a", "s0")),
    )

    solution = solve(game)

    assert solution.winning_regions[1] == {"s0"}
    assert solution.winning_regions[0] == set()


def test_solve_handles_genuine_multicolor_parity_without_crashing():
    # Regression test: for a losing owner, spot.get_strategy() can return
    # edge numbers with no corresponding edge in our automaton at all (not
    # just the documented "0 = none" sentinel), SWIG surfaces some of these
    # as huge unsigned values (e.g. a C++ -5 as 4294967291). Only reproduces
    # with >2 real colors and a player that loses everywhere; forces player
    # 1 to lose since it doesn't control the hub's self-loop at all.
    ts = TransitionSystem()
    ts.add_transition("hub", "both", "int_both")
    ts.add_transition("hub", "aonly", "int_aonly")
    ts.add_transition("hub", "bonly", "int_bonly")
    ts.add_transition("hub", "neither", "int_neither")
    for intermediate in ("int_both", "int_aonly", "int_bonly", "int_neither"):
        ts.add_transition(intermediate, "loop", "hub")
    ts.add_state("hub", initial=True)

    game = Game(
        arena=ts,
        player_states={0: {"hub"}, 1: {"int_both", "int_aonly", "int_bonly", "int_neither"}},
        objective=AcceptanceCondition(
            kind=AcceptanceKind.PARITY,
            parity_kind=ParityKind.MAX,
            parity_style=ParityStyle.ODD,
            priorities={
                ("int_both", "loop", "hub"): 1,
                ("int_aonly", "loop", "hub"): 2,
                ("int_bonly", "loop", "hub"): 0,
                ("int_neither", "loop", "hub"): 2,
            },
        ),
    )

    solution = solve(game)  # must not raise KeyError

    assert solution.winning_regions[0] == ts.states
    assert solution.winning_regions[1] == set()
    assert solution.strategies[0].move("hub") == "both"


def test_solve_requires_objective():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    game = Game(arena=ts, player_states={0: {"s0"}, 1: set()})

    with pytest.raises(ValueError, match="objective"):
        solve(game)


def test_solve_supports_multiple_initial_states():
    # forced cycle, no accepting transition marked anywhere: Büchi rejects,
    # so player 0 loses from *both* declared initial states, not just
    # whichever one solve() happens to anchor on internally.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s1", "a", "s0")
    ts.add_state("s0", initial=True)
    ts.add_state("s1", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0", "s1"}, 1: set()},
        objective=_buchi_objective(),
    )

    solution = solve(game)

    assert solution.winning_regions[1] == {"s0", "s1"}
    assert solution.winning_regions[0] == set()


def test_solve_gives_correct_verdict_for_every_initial_state_not_just_one():
    # Two disconnected components, each with its own initial state: s0
    # (marked, player 0 wins) and t0 (unmarked-forever, player 0 loses).
    # Before the reachability-anchor fix, only one of these could be solved
    # correctly by declaring a single initial state.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_transition("t0", "a", "t0")
    ts.add_state("s0", initial=True)
    ts.add_state("t0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0", "t0"}, 1: set()},
        objective=_buchi_objective(("s0", "a", "s0")),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"s0"}
    assert solution.winning_regions[1] == {"t0"}


def test_solve_requires_at_least_one_state():
    ts = TransitionSystem()
    game = Game(arena=ts, player_states={0: set(), 1: set()}, objective=_buchi_objective())

    with pytest.raises(ValueError, match="at least one state"):
        solve(game)


def test_solve_gives_correct_verdict_even_for_a_state_never_marked_initial():
    # Regression test: the reachability anchor used to bridge only to
    # game.arena.initial_states, so a winning state that was simply never
    # declared initial (e.g. a state product()'s BFS reaches but never
    # seeds from) could be silently misreported as a loss, since Spot
    # defaults winners to false for anything unreachable from its own init.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_transition("t0", "a", "t0")  # t0 is never marked initial=True
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0", "t0"}, 1: set()},
        objective=_buchi_objective(("s0", "a", "s0"), ("t0", "a", "t0")),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"s0", "t0"}


def test_solve_requires_every_state_owned_by_exactly_one_player():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    game = Game(arena=ts, player_states={0: set(), 1: set()}, objective=_buchi_objective())

    with pytest.raises(ValueError, match="exactly one"):
        solve(game)


def test_solve_rejects_a_nondeterministic_arena():
    # Strategy only records the chosen action, not which successor it led
    # to, so an ambiguous (state, action) -> {multiple targets} can't be
    # soundly turned into a Strategy the caller could actually replay.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s0", "a", "s2")
    ts.add_state("s0", initial=True)
    game = Game(arena=ts, player_states={0: {"s0", "s1", "s2"}, 1: set()}, objective=_buchi_objective())

    with pytest.raises(ValueError, match="deterministic"):
        solve(game)


def test_solve_requires_spot():
    import model_checker.automata.games.solver as solver_module

    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    game = Game(arena=ts, player_states={0: {"s0"}, 1: set()}, objective=_buchi_objective())

    original_spot = solver_module.spot
    solver_module.spot = None
    try:
        with pytest.raises(ImportError):
            solve(game)
    finally:
        solver_module.spot = original_spot


def test_solve_raises_if_spot_returns_the_wrong_number_of_state_winners(monkeypatch):
    # spot.get_state_winners()/get_strategy() are expected to return exactly
    # one entry per arena state plus one for the internal reachability
    # anchor (see solve()'s own docstring); a mismatch here has bitten this
    # project before (malformed edge numbers on genuine 3+-color parity
    # games), so a wrong-length return must fail loudly, not silently zip
    # states to the wrong winners.
    import model_checker.automata.games.solver as solver_module

    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    game = Game(arena=ts, player_states={0: {"s0"}, 1: set()}, objective=_buchi_objective(("s0", "a", "s0")))

    real_get_state_winners = solver_module.spot.get_state_winners
    monkeypatch.setattr(
        solver_module.spot,
        "get_state_winners",
        lambda aut: real_get_state_winners(aut)[:-1],
    )

    with pytest.raises(RuntimeError, match="unexpected number of"):
        solve(game)


def test_parity_objective_with_no_priorities_defaults_to_a_single_color():
    # No transition ever needs marking, e.g. a translated "always true" LTL
    # formula. Single-color max-odd reduces to Fin(0): trivially satisfied
    # since color 0 is never visited, so player 0 wins everywhere, not an
    # error.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0"}, 1: set()},
        objective=AcceptanceCondition(kind=AcceptanceKind.PARITY, parity_kind=ParityKind.MAX, parity_style=ParityStyle.ODD),
    )

    solution = solve(game)

    assert solution.winning_regions[0] == {"s0"}


def test_parity_objective_with_no_priorities_and_even_style_rejects():
    # Mirror case: single-color max-even reduces to Inf(0), never satisfied
    # since color 0 is never visited, so player 0 loses everywhere.
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    game = Game(
        arena=ts,
        player_states={0: {"s0"}, 1: set()},
        objective=AcceptanceCondition(kind=AcceptanceKind.PARITY, parity_kind=ParityKind.MAX, parity_style=ParityStyle.EVEN),
    )

    solution = solve(game)

    assert solution.winning_regions[1] == {"s0"}
