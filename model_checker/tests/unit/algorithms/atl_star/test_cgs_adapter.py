"""The ATL* adapter turns a CGS into a transition system over joint actions.

The toy CGS (toy_cgs.py): from s0 only req|grant reaches s1; every other joint
action stays at s0; from s1 every joint action returns to s0.
"""

from __future__ import annotations

import pytest

from model_checker.algorithms.explicit.ATL_STAR.cgs_adapter import _joint_action, adapt
from model_checker.tests.unit.algorithms.atl_star.toy_cgs import (
    AllWildcardToyCGS,
    BadInitialStateToyCGS,
    CompactActionCGS,
    MalformedToyCGS,
    ToyCGS,
    WildcardToyCGS,
)

pytestmark = pytest.mark.atl_star

_JOINTS = [("req", "grant"), ("req", "deny"), ("idle", "grant"), ("idle", "deny")]


def _act(agent1: str, agent2: str) -> frozenset:
    return frozenset({(1, agent1), (2, agent2)})


def test_states_initial_state_propositions_and_labels():
    """The adapter keeps the model's states, initial state and labelling."""
    result = adapt(ToyCGS())
    assert result.transition_system.states == {"s0", "s1"}
    assert result.transition_system.initial_states == {"s0"}
    assert result.propositions == frozenset({"granted"})
    assert result.labels == {"s0": frozenset(), "s1": frozenset({"granted"})}


@pytest.mark.parametrize("cgs_class", [ToyCGS, WildcardToyCGS])
def test_successors_under_each_joint_action(cgs_class):
    """Only req|grant leaves s0; a `*` cell gives the same self-loops as listing them."""
    ts = adapt(cgs_class()).transition_system
    assert ts.successors("s0", _act("req", "grant")) == {"s1"}
    for joint in _JOINTS[1:]:
        assert ts.successors("s0", _act(*joint)) == {"s0"}


def test_every_joint_action_from_s1_returns_to_s0():
    """s1 has one cell listing all four joint actions back to s0."""
    ts = adapt(ToyCGS()).transition_system
    assert all(ts.successors("s1", _act(*joint)) == {"s0"} for joint in _JOINTS)


def test_model_with_only_wildcards_loops_instead_of_deadlocking():
    """No concrete action anywhere, so `*` itself must become the self-loop."""
    ts = adapt(AllWildcardToyCGS()).transition_system
    assert ts.successors("s0", frozenset({(1, "*")})) == {"s0"}


def test_wildcard_in_a_real_fixture_absorbs_every_joint_action(cgs_simple_parser):
    """s3 of atl_2agents_4states_simple.txt is a `*` self-loop."""
    ts = adapt(cgs_simple_parser).transition_system
    for joint in [("A", "C"), ("A", "D"), ("B", "C"), ("B", "D")]:
        assert ts.successors("s3", _act(*joint)) == {"s3"}


def test_compact_cells_of_a_real_model():
    """`AC` is agent 1 playing A and agent 2 playing C."""
    ts = adapt(CompactActionCGS()).transition_system
    assert ts.successors("s0", _act("A", "C")) == {"s1"}
    assert ts.successors("s0", _act("A", "D")) == {"s0"}


@pytest.mark.parametrize(
    ("cell", "joint"),
    [
        ("AC", _act("A", "C")),
        ("req|grant", _act("req", "grant")),
        ("I|IDLE", _act("IDLE", "IDLE")),
    ],
)
def test_joint_action_reads_compact_piped_and_idle_forms(cell, joint):
    """One letter per agent, or `|` between tokens; `I` is the idle action."""
    assert _joint_action(cell, 2) == joint


@pytest.mark.parametrize(
    ("make", "name"),
    [
        (lambda: _joint_action("r", 2), "'r'"),
        (lambda: adapt(MalformedToyCGS()), "'r'"),
        (lambda: adapt(BadInitialStateToyCGS()), "s99"),
    ],
    ids=["too_few_tokens", "malformed_profile_in_a_model", "unknown_initial_state"],
)
def test_bad_input_is_refused_by_name(make, name):
    """The message names the bad profile or state."""
    with pytest.raises(ValueError, match=name):
        make()
