"""CGS joint-action normalization: compact and explicit profiles are equivalent."""

import pytest

from model_checker.parsers.game_structures.cgs.cgs_actions import (
    build_action_list,
    extract_actions_for_agents,
    parse_joint_action_cell,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "cell,num_agents,expected",
    [
        ("AC,AD", 2, ["A|C", "A|D"]),
        ("A|C,A|D", 2, ["A|C", "A|D"]),
        ("AC,BC", 2, ["A|C", "B|C"]),
        ("*", 2, ["*|*"]),
        ("*", 3, ["*|*|*"]),
        ("a", 1, ["a"]),
        ("I", 1, ["IDLE"]),
        ("IDLE|MOVE", 2, ["IDLE|MOVE"]),
        ("MOVE_FORWARD", 1, ["MOVE_FORWARD"]),
        ("IDLE", 1, ["IDLE"]),
        ("MOVE_FORWARD|BLOCK_PATH,IDLE|IDLE", 2, ["MOVE_FORWARD|BLOCK_PATH", "IDLE|IDLE"]),
    ],
)
def test_build_action_list_normalizes_joints(cell, num_agents, expected):
    """Compact and explicit cells expand to the same pipe-separated profiles."""
    assert build_action_list(cell, num_agents) == expected


@pytest.mark.unit
def test_compact_and_explicit_cells_match():
    """AC,AD and A|C,A|D produce identical normalized profile lists."""
    assert build_action_list("AC,AD", 2) == build_action_list("A|C,A|D", 2)


@pytest.mark.unit
@pytest.mark.parametrize(
    "cell,num_agents",
    [
        ("MOVE_FORWARD|BLOCK_PATH|EXTRA", 2),
        ("ABC", 2),
        ("MOVE_FORWARD|", 2),
        ("|BLOCK_PATH", 2),
        ("MOVE_FORWARD|BLOCK_PATH,", 2),
    ],
)
def test_strict_joint_actions_reject_malformed_arity(cell, num_agents):
    with pytest.raises(ValueError):
        parse_joint_action_cell(cell, num_agents, strict_arity=True)


@pytest.mark.unit
def test_legacy_positional_notation_remains_supported():
    assert parse_joint_action_cell("II,AB,CD", 2) == [
        ["IDLE", "IDLE"], ["A", "B"], ["C", "D"]
    ]
    assert parse_joint_action_cell("MOVE_FORWARD", 1) == [["MOVE_FORWARD"]]
    assert parse_joint_action_cell("IDLE", 1) == [["IDLE"]]
    assert parse_joint_action_cell("MOVE_FORWARD|BLOCK_PATH", 2, strict_arity=True) == [
        ["MOVE_FORWARD", "BLOCK_PATH"]
    ]
    # VITAMIN's historical permissive behavior is intentionally unchanged.
    assert parse_joint_action_cell("ABC", 2) == [["A", "B"]]


@pytest.mark.unit
def test_extract_actions_for_partial_coalition_uses_full_joint_arity():
    """Selecting agent 1 in a 2-agent CGS must not turn AB into action AB."""
    actions = extract_actions_for_agents([["AB,CD"]], [1], num_agents=2)
    assert set(actions["agent1"]) == {"A", "C"}
    nominal = extract_actions_for_agents(
        [["MOVE_FORWARD|BLOCK_PATH,IDLE|IDLE"]], [1], num_agents=2
    )
    assert set(nominal["agent1"]) == {"MOVE_FORWARD", "IDLE"}
