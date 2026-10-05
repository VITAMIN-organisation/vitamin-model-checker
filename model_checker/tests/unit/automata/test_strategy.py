"""Tests for games/strategy.py's Strategy. Pure Python, no Spot dependency,
Strategy is a plain dataclass wrapper (state -> action), exercised
end-to-end via solver.py/_attractor_oracle.py elsewhere, but tested in
isolation here."""

import pytest

from model_checker.automata.games.strategy import Strategy


def _joint(**player_actions):
    """Same JointAction shape as arena.py: frozenset[(player_id, action)]."""
    return frozenset(player_actions.items())


def test_move_returns_recorded_action_for_known_state():
    strategy = Strategy({"s0": "a", "s1": "b"})
    assert strategy.move("s0") == "a"
    assert strategy.move("s1") == "b"


def test_move_returns_none_for_unknown_state():
    strategy = Strategy({"s0": "a"})
    assert strategy.move("unknown") is None


def test_move_works_with_non_joint_plain_actions():
    # e.g. games/_attractor_oracle.py's reachability strategies, whose
    # actions are arbitrary symbols, not joint actions.
    strategy = Strategy({"s0": "escape", "s1": "stall"})
    assert strategy.move("s0") == "escape"


def test_project_extracts_one_players_action_from_joint_actions():
    strategy = Strategy({
        "s0": _joint(A="a1", B="b1"),
        "s1": _joint(A="a2", B="b2"),
    })

    projected_a = strategy.project("A")

    assert projected_a.move("s0") == "a1"
    assert projected_a.move("s1") == "a2"


def test_project_for_different_players_gives_independent_strategies():
    strategy = Strategy({"s0": _joint(A="a1", B="b1")})

    projected_a = strategy.project("A")
    projected_b = strategy.project("B")

    assert projected_a.move("s0") == "a1"
    assert projected_b.move("s0") == "b1"
    # projecting doesn't mutate the original joint-action strategy
    assert strategy.move("s0") == _joint(A="a1", B="b1")


def test_project_handles_coalitions_of_more_than_two_players():
    strategy = Strategy({"s0": _joint(A="a1", B="b1", C="c1")})

    assert strategy.project("C").move("s0") == "c1"


def test_project_raises_a_clear_error_for_a_player_absent_from_the_joint_action():
    strategy = Strategy({"s0": _joint(A="a1", B="b1")})

    with pytest.raises(ValueError, match="C"):
        strategy.project("C")


def test_default_choices_are_not_shared_between_instances():
    a = Strategy()
    b = Strategy()
    assert a.choices is not b.choices
