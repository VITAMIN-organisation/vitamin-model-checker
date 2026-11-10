"""Transition systems and the concurrent-to-turn-based game construction.

In the concurrent system agent A (the coalition) and B move together: from s0,
A's a1 leads to s1 or s2 depending on B, and A's a2 stays at s0. The turn-based
game puts an intermediate state after A's choice where B then picks.
"""

from model_checker.automata.games.arena import concurrent_to_turnbased, remap_priorities
from model_checker.automata.transition_system import TransitionSystem


def _joint(**player_actions):
    return frozenset(player_actions.items())


def _concurrent_system():
    ts = TransitionSystem()
    ts.add_transition("s0", _joint(A="a1", B="b1"), "s1")
    ts.add_transition("s0", _joint(A="a1", B="b2"), "s2")
    ts.add_transition("s0", _joint(A="a2", B="b1"), "s0")
    ts.add_state("s0", initial=True)
    return ts


def _turnbased():
    return concurrent_to_turnbased(_concurrent_system(), controlled_players={"A"})


def _after(game, action):
    """The one intermediate state reached when A plays `action` at s0."""
    [intermediate] = game.arena.successors("s0", frozenset({("A", action)}))
    return intermediate


def test_transitions_register_states_and_may_branch():
    """Adding a -> b and a -> c records both successors and both states."""
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s0", "a", "s2")
    ts.add_state("s3", initial=True)
    assert ts.states == {"s0", "s1", "s2", "s3"}
    assert ts.initial_states == {"s3"}
    assert ts.successors("s0", "a") == {"s1", "s2"}
    assert ts.successors("s0", "b") == set()
    assert ts.successors("nope", "a") == set()


def test_original_states_belong_to_the_coalition():
    """s0, s1 and s2 are player 0's; the initial state is kept."""
    game = _turnbased()
    assert game.player_states[0] == {"s0", "s1", "s2"}
    assert game.arena.initial_states == {"s0"}
    assert game.objective is None


def test_coalition_choice_leads_to_one_opponent_state_per_choice():
    """a1 and a2 each lead to their own intermediate, owned by player 1."""
    game = _turnbased()
    after_a1, after_a2 = _after(game, "a1"), _after(game, "a2")
    assert after_a1 != after_a2
    assert {after_a1, after_a2} <= game.player_states[1]
    assert not {after_a1, after_a2} & game.player_states[0]


def test_opponent_choice_recovers_the_original_successor():
    """After a1, B's b1 gives s1 and b2 gives s2; after a2, b1 gives s0."""
    game = _turnbased()
    after_a1 = _after(game, "a1")
    assert game.arena.successors(after_a1, frozenset({("B", "b1")})) == {"s1"}
    assert game.arena.successors(after_a1, frozenset({("B", "b2")})) == {"s2"}
    assert game.arena.successors(_after(game, "a2"), frozenset({("B", "b1")})) == {"s0"}


def test_priorities_move_to_the_opponent_edge_of_each_transition():
    """Two transitions share A's a1; their priorities 2 and 4 stay apart on B's edges."""
    game = _turnbased()
    remapped = remap_priorities(
        {
            ("s0", _joint(A="a1", B="b1"), "s1"): 2,
            ("s0", _joint(A="a1", B="b2"), "s2"): 4,
        },
        controlled_players={"A"},
    )
    assert {target: priority for (_, _, target), priority in remapped.items()} == {
        "s1": 2,
        "s2": 4,
    }
    for source, symbol, target in remapped:
        assert target in game.arena.successors(source, symbol)
