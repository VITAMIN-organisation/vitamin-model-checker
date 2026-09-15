from __future__ import annotations

import pytest

from model_checker.algorithms.explicit.ATL_STAR.cgs_adapter import (
    _joint_action,
    adapt,
)
from model_checker.tests.unit.algorithms.atl_star.toy_cgs import (
    BadInitialStateToyCGS,
    CompactActionCGS,
    MalformedToyCGS,
    ToyCGS,
    WildcardToyCGS,
)


def test_states_and_initial_state():
    result = adapt(ToyCGS())
    assert result.transition_system.states == {"s0", "s1"}
    assert result.transition_system.initial_states == {"s0"}


def test_players_are_one_based():
    result = adapt(ToyCGS())
    assert result.players == (1, 2)


def test_grant_transition_is_the_only_way_to_reach_s1():
    result = adapt(ToyCGS())
    ts = result.transition_system
    grant = frozenset({(1, "req"), (2, "grant")})
    assert ts.successors("s0", grant) == {"s1"}


def test_every_other_joint_action_self_loops_on_s0():
    result = adapt(ToyCGS())
    ts = result.transition_system
    for agent1, agent2 in [("req", "deny"), ("idle", "grant"), ("idle", "deny")]:
        action = frozenset({(1, agent1), (2, agent2)})
        assert ts.successors("s0", action) == {"s0"}


def test_s1_resets_to_s0_under_every_joint_action():
    result = adapt(ToyCGS())
    ts = result.transition_system
    for agent1, agent2 in [("req", "grant"), ("req", "deny"), ("idle", "grant"), ("idle", "deny")]:
        action = frozenset({(1, agent1), (2, agent2)})
        assert ts.successors("s1", action) == {"s0"}


def test_labels_reflect_matrix_prop():
    result = adapt(ToyCGS())
    assert result.labels["s0"] == frozenset()
    assert result.labels["s1"] == frozenset({"granted"})


def test_malformed_profile_raises():
    with pytest.raises(ValueError, match="'r'"):
        adapt(MalformedToyCGS())


def test_unknown_initial_state_raises():
    with pytest.raises(ValueError, match="s99"):
        adapt(BadInitialStateToyCGS())


def test_wildcard_cell_self_loops_on_every_action_not_already_used_from_that_state():
    result = adapt(WildcardToyCGS())
    ts = result.transition_system
    grant = frozenset({(1, "req"), (2, "grant")})
    # The explicit s0 -> s1 transition survives untouched...
    assert ts.successors("s0", grant) == {"s1"}
    # ...and every other joint action known to the model self-loops on s0,
    # exactly like plain ToyCGS's own hand-written self-loop cell.
    for agent1, agent2 in [("req", "deny"), ("idle", "grant"), ("idle", "deny")]:
        action = frozenset({(1, agent1), (2, agent2)})
        assert ts.successors("s0", action) == {"s0"}


def test_joint_action_supports_the_compact_one_character_per_agent_form():
    # Confirmed against VITAMIN's own cgs_actions.parse_joint_action_cell:
    # no "|" at all means one character per agent, e.g. "AC" = agent 1 does
    # A, agent 2 does C.
    assert _joint_action("AC", 2) == frozenset({(1, "A"), (2, "C")})


def test_joint_action_still_supports_the_pipe_separated_form():
    assert _joint_action("req|grant", 2) == frozenset({(1, "req"), (2, "grant")})


def test_joint_action_tolerates_extra_tokens_like_the_real_parser_does():
    # cgs_actions.parse_joint_action_cell only requires *at least*
    # number_of_agents tokens/characters, silently dropping the rest.
    assert _joint_action("req|grant|extra", 2) == frozenset({(1, "req"), (2, "grant")})
    assert _joint_action("ABC", 2) == frozenset({(1, "A"), (2, "B")})


def test_joint_action_normalizes_idle_tokens():
    assert _joint_action("I|IDLE", 2) == frozenset({(1, "IDLE"), (2, "IDLE")})


def test_joint_action_rejects_too_few_tokens():
    with pytest.raises(ValueError, match="'r'"):
        _joint_action("r", 2)


def test_adapt_handles_a_real_cgs_using_the_compact_action_format():
    result = adapt(CompactActionCGS())
    ts = result.transition_system
    assert ts.successors("s0", frozenset({(1, "A"), (2, "C")})) == {"s1"}
    assert ts.successors("s0", frozenset({(1, "A"), (2, "D")})) == {"s0"}


def test_adapt_expands_the_wildcard_in_a_real_vitamin_fixture(cgs_simple_parser):
    # atl_2agents_4states_simple.txt, loaded via the real CGS class: s3's
    # self-loop is a real "*" cell, absorbing under every joint action the
    # rest of this fixture uses (AC/AD/BC/BD all appear on other rows).
    result = adapt(cgs_simple_parser)
    ts = result.transition_system
    for agent1, agent2 in [("A", "C"), ("A", "D"), ("B", "C"), ("B", "D")]:
        action = frozenset({(1, agent1), (2, agent2)})
        assert ts.successors("s3", action) == {"s3"}
