"""Cross-validates games/solver.py (Spot-backed) against
games/_attractor_oracle.py (hand-written) on small hand-built games.
Requires Spot, see tests/test_automaton.py.

Reachability and Büchi coincide once every terminal state is turned into a
self-loop (Spot's game model needs deadlock-free/infinite plays; the oracle
doesn't) and the "target" self-loop is marked as the sole accepting edge:
looping on target forever is exactly "reachability of target" restated as
an infinitary condition.
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceCondition, AcceptanceKind
from model_checker.automata.games._attractor_oracle import solve_reachability
from model_checker.automata.games.game import Game
from model_checker.automata.games.solver import solve
from model_checker.automata.transition_system import TransitionSystem


def _as_buchi_game(ts: TransitionSystem, player_states, target: str) -> Game:
    return Game(
        arena=ts,
        player_states=player_states,
        objective=AcceptanceCondition(kind=AcceptanceKind.BUCHI, priorities={(target, "loop", target): 0}),
    )


def _reachability_game(ts: TransitionSystem, player_states) -> Game:
    return Game(arena=ts, player_states=player_states)


def _assert_regions_agree(ts, player_states, target):
    oracle = solve_reachability(_reachability_game(ts, player_states), player=0, target={target})
    spot_solution = solve(_as_buchi_game(ts, player_states, target))

    assert spot_solution.winning_regions[0] == oracle.winning_regions[0]
    assert spot_solution.winning_regions[1] == oracle.winning_regions[1]


def test_agree_on_forced_chain_to_target():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s1", "a", "target")
    ts.add_transition("target", "loop", "target")
    ts.add_state("s0", initial=True)

    _assert_regions_agree(ts, {0: {"s0", "s1", "target"}, 1: set()}, "target")


def test_agree_when_opponent_has_an_escape_route():
    ts = TransitionSystem()
    ts.add_transition("s0", "escape", "target")
    ts.add_transition("s0", "stall", "dead_end")
    ts.add_transition("target", "loop", "target")
    ts.add_transition("dead_end", "loop", "dead_end")
    ts.add_state("s0", initial=True)

    _assert_regions_agree(ts, {0: {"target", "dead_end"}, 1: {"s0"}}, "target")


def test_agree_when_opponent_is_forced_into_target_regardless_of_choice():
    ts = TransitionSystem()
    ts.add_transition("s0", "left", "target")
    ts.add_transition("s0", "right", "target")
    ts.add_transition("target", "loop", "target")
    ts.add_state("s0", initial=True)

    _assert_regions_agree(ts, {0: {"target"}, 1: {"s0"}}, "target")


def test_agree_on_a_larger_branching_game():
    # s0 (player0) picks left (into s1, where the opponent can still escape
    # to a dead end) or right (into s2, forced straight through to target
    # with no real choice), the winning move is "right", not "left".
    ts = TransitionSystem()
    ts.add_transition("s0", "left", "s1")
    ts.add_transition("s0", "right", "s2")
    ts.add_transition("s1", "advance", "target")
    ts.add_transition("s1", "retreat", "dead_end")
    ts.add_transition("s2", "advance", "target")
    ts.add_transition("target", "loop", "target")
    ts.add_transition("dead_end", "loop", "dead_end")
    ts.add_state("s0", initial=True)

    player_states = {0: {"s0", "s2", "target", "dead_end"}, 1: {"s1"}}
    _assert_regions_agree(ts, player_states, "target")
