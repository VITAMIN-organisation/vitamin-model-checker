"""Tests for the hand-written reachability attractor (test oracle only).
Pure Python, no Spot dependency."""

from model_checker.automata.games._attractor_oracle import (
    attractor,
    solve_reachability,
)
from model_checker.automata.games.game import Game
from model_checker.automata.transition_system import TransitionSystem


def _linear_chain():
    """s0 -a-> s1 -a-> s2 -a-> s3, all owned by player 0. Only one action
    per state, so reaching s3 is forced no matter who "chooses"."""
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s1", "a", "s2")
    ts.add_transition("s2", "a", "s3")
    ts.add_state("s3")
    return ts


def test_attractor_reaches_target_through_forced_chain():
    ts = _linear_chain()
    player_states = {0: ts.states, 1: set()}
    win_region, strategy = attractor(ts, player_states, player=0, target={"s3"})

    assert win_region == {"s0", "s1", "s2", "s3"}
    assert strategy.move("s0") == "a"
    assert strategy.move("s1") == "a"
    assert strategy.move("s2") == "a"


def test_attractor_excludes_states_that_cannot_reach_target():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("unreachable", "a", "unreachable")
    player_states = {0: ts.states, 1: set()}

    win_region, _ = attractor(ts, player_states, player=0, target={"s1"})

    assert win_region == {"s0", "s1"}
    assert "unreachable" not in win_region


def test_opponent_owned_state_needs_all_actions_to_land_in_attractor():
    """s0 is owned by the opponent (player 1) with two actions: one escapes
    to the target, one loops back to a dead end. Player 0 should NOT be able
    to force reaching the target through s0, since the opponent picks."""
    ts = TransitionSystem()
    ts.add_transition("s0", "escape", "target")
    ts.add_transition("s0", "stall", "dead_end")
    ts.add_state("dead_end")
    player_states = {0: set(), 1: {"s0"}}

    win_region, _ = attractor(ts, player_states, player=0, target={"target"})

    assert "s0" not in win_region
    assert win_region == {"target"}


def test_opponent_owned_state_joins_when_every_action_reaches_target():
    ts = TransitionSystem()
    ts.add_transition("s0", "left", "target")
    ts.add_transition("s0", "right", "target")
    player_states = {0: set(), 1: {"s0"}}

    win_region, _ = attractor(ts, player_states, player=0, target={"target"})

    assert win_region == {"s0", "target"}


def test_solve_reachability_returns_complementary_winning_regions():
    ts = _linear_chain()
    game = Game(arena=ts, player_states={0: ts.states, 1: set()})

    solution = solve_reachability(game, player=0, target={"s3"})

    assert solution.winning_regions[0] == {"s0", "s1", "s2", "s3"}
    assert solution.winning_regions[1] == set()
    assert solution.strategies[0].move("s0") == "a"
