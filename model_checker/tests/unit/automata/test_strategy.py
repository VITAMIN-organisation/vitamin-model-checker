"""A strategy maps states to moves; a joint-action strategy projects to each player's own moves."""

import pytest

from model_checker.automata.games.strategy import Strategy


def _joint(**player_actions):
    return frozenset(player_actions.items())


def test_move_is_the_recorded_choice_or_none():
    """An unknown state has no move rather than an error."""
    strategy = Strategy({"s0": "a"})
    assert strategy.move("s0") == "a"
    assert strategy.move("unknown") is None


def test_projection_gives_each_player_its_own_action():
    """A, B and C each get their part of the joint action, and the original is unchanged."""
    strategy = Strategy(
        {"s0": _joint(A="a1", B="b1", C="c1"), "s1": _joint(A="a2", B="b2", C="c2")}
    )
    assert [strategy.project("A").move(s) for s in ("s0", "s1")] == ["a1", "a2"]
    assert strategy.project("C").move("s0") == "c1"
    assert strategy.move("s0") == _joint(A="a1", B="b1", C="c1")


def test_projection_on_a_player_outside_the_joint_action_is_an_error():
    """The message names the missing player."""
    with pytest.raises(ValueError, match="C"):
        Strategy({"s0": _joint(A="a1", B="b1")}).project("C")
