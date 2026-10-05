"""Tests for concurrent_to_turnbased(). Pure Python, no Spot dependency."""

from model_checker.automata.games.arena import (
    concurrent_to_turnbased,
    remap_priorities,
)


def _joint(**player_actions):
    return frozenset(player_actions.items())


def _toy_concurrent_system():
    """2 agents, A (to be controlled) and B (opponent). From s0: A always
    picks between a1/a2; B's response only matters when A picks a1."""
    from model_checker.automata.transition_system import TransitionSystem

    ts = TransitionSystem()
    ts.add_transition("s0", _joint(A="a1", B="b1"), "s1")
    ts.add_transition("s0", _joint(A="a1", B="b2"), "s2")
    ts.add_transition("s0", _joint(A="a2", B="b1"), "s0")
    ts.add_state("s0", initial=True)
    return ts


def test_original_states_stay_player0_and_are_preserved():
    game = concurrent_to_turnbased(_toy_concurrent_system(), controlled_players={"A"})
    assert game.player_states[0] == {"s0", "s1", "s2"}
    assert game.arena.initial_states == {"s0"}


def test_coalition_choice_leads_to_a_shared_intermediate_player1_state():
    game = concurrent_to_turnbased(_toy_concurrent_system(), controlled_players={"A"})
    coalition_a1 = frozenset({("A", "a1")})
    intermediates = game.arena.successors("s0", coalition_a1)
    assert len(intermediates) == 1
    intermediate = next(iter(intermediates))
    assert intermediate in game.player_states[1]
    assert intermediate not in game.player_states[0]


def test_opponent_choice_at_intermediate_recovers_original_successors():
    game = concurrent_to_turnbased(_toy_concurrent_system(), controlled_players={"A"})
    coalition_a1 = frozenset({("A", "a1")})
    intermediate = next(iter(game.arena.successors("s0", coalition_a1)))

    assert game.arena.successors(intermediate, frozenset({("B", "b1")})) == {"s1"}
    assert game.arena.successors(intermediate, frozenset({("B", "b2")})) == {"s2"}


def test_different_coalition_choices_get_different_intermediates():
    game = concurrent_to_turnbased(_toy_concurrent_system(), controlled_players={"A"})
    inter_a1 = next(iter(game.arena.successors("s0", frozenset({("A", "a1")}))))
    inter_a2 = next(iter(game.arena.successors("s0", frozenset({("A", "a2")}))))
    assert inter_a1 != inter_a2
    assert game.arena.successors(inter_a2, frozenset({("B", "b1")})) == {"s0"}


def test_objective_is_left_for_caller_to_set():
    game = concurrent_to_turnbased(_toy_concurrent_system(), controlled_players={"A"})
    assert game.objective is None


def test_remap_priorities_lands_on_real_arena_edges():
    game = concurrent_to_turnbased(_toy_concurrent_system(), controlled_players={"A"})
    # two ts transitions share a coalition choice (A=a1) but disagree on
    # priority via their opponent response, only the second (unique) arena
    # edge per transition can carry that distinction
    ts_priorities = {
        ("s0", _joint(A="a1", B="b1"), "s1"): 2,
        ("s0", _joint(A="a1", B="b2"), "s2"): 4,
    }

    remapped = remap_priorities(ts_priorities, controlled_players={"A"})

    assert len(remapped) == 2
    for source, symbol, target in remapped:
        assert target in game.arena.successors(source, symbol)


def test_remap_priorities_distinguishes_transitions_sharing_a_coalition_choice():
    ts_priorities = {
        ("s0", _joint(A="a1", B="b1"), "s1"): 2,
        ("s0", _joint(A="a1", B="b2"), "s2"): 4,
    }
    remapped = remap_priorities(ts_priorities, controlled_players={"A"})

    by_target = {target: priority for (_source, _symbol, target), priority in remapped.items()}
    assert by_target == {"s1": 2, "s2": 4}
