"""The Spot-backed solver and a hand-written attractor agree with the regions worked out by hand.

Reachability of `target` is the Büchi condition "loop on target forever" once
every terminal state has a self-loop (Spot needs infinite plays). Player 0 wants
`target`; player 1 owns the states listed for it and picks against player 0.
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceCondition, AcceptanceKind
from model_checker.automata.games.game import Game
from model_checker.automata.games.solver import solve
from model_checker.automata.transition_system import TransitionSystem
from model_checker.tests.helpers.attractor_oracle import solve_reachability


def _arena(*edges):
    ts = TransitionSystem()
    for source, action, target in edges:
        ts.add_transition(source, action, target)
    ts.add_state("s0", initial=True)
    return ts


_LOOPS = [("target", "loop", "target"), ("dead_end", "loop", "dead_end")]

_CASES = [
    (
        "forced_chain",
        [("s0", "a", "s1"), ("s1", "a", "target"), ("target", "loop", "target")],
        set(),
        {0: {"s0", "s1", "target"}, 1: set()},
    ),
    (
        "opponent_escapes",
        [("s0", "escape", "target"), ("s0", "stall", "dead_end"), *_LOOPS],
        {"s0"},
        {0: {"target"}, 1: {"s0", "dead_end"}},
    ),
    (
        "opponent_has_no_way_out",
        [
            ("s0", "left", "target"),
            ("s0", "right", "target"),
            ("target", "loop", "target"),
        ],
        {"s0"},
        {0: {"s0", "target"}, 1: set()},
    ),
    (
        "player_picks_the_safe_branch",
        [
            ("s0", "left", "s1"),
            ("s0", "right", "s2"),
            ("s1", "advance", "target"),
            ("s1", "retreat", "dead_end"),
            ("s2", "advance", "target"),
            *_LOOPS,
        ],
        {"s1"},
        {0: {"s0", "s2", "target"}, 1: {"s1", "dead_end"}},
    ),
]


@pytest.mark.parametrize(
    ("edges", "opponent_states", "regions"),
    [case[1:] for case in _CASES],
    ids=[case[0] for case in _CASES],
)
def test_both_solvers_find_the_hand_computed_regions(edges, opponent_states, regions):
    """Player 0 wins exactly where it can force target; the opponent wins the rest."""
    ts = _arena(*edges)
    player_states = {0: ts.states - opponent_states, 1: opponent_states}
    oracle = solve_reachability(
        Game(arena=ts, player_states=player_states), 0, {"target"}
    )
    spot_solution = solve(
        Game(
            arena=ts,
            player_states=player_states,
            objective=AcceptanceCondition(
                kind=AcceptanceKind.BUCHI, priorities={("target", "loop", "target"): 0}
            ),
        )
    )
    for solution in (oracle, spot_solution):
        assert solution.winning_regions[0] == regions[0]
        assert solution.winning_regions[1] == regions[1]


def test_attractor_strategy_picks_the_safe_branch():
    """At s0 the oracle must choose `right`; `left` lets the opponent retreat."""
    ts = _arena(*_CASES[3][1])
    player_states = {0: ts.states - {"s1"}, 1: {"s1"}}
    solution = solve_reachability(
        Game(arena=ts, player_states=player_states), 0, {"target"}
    )
    assert solution.strategies[0].move("s0") == "right"
