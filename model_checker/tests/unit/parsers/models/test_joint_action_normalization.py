"""CGS joint-action normalization: compact and explicit profiles are equivalent."""

import pytest

from model_checker.parsers.game_structures.cgs.cgs_actions import build_action_list


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
    ],
)
def test_build_action_list_normalizes_joints(cell, num_agents, expected):
    """Compact and explicit cells expand to the same pipe-separated profiles."""
    assert build_action_list(cell, num_agents) == expected


@pytest.mark.unit
def test_compact_and_explicit_cells_match():
    """AC,AD and A|C,A|D produce identical normalized profile lists."""
    assert build_action_list("AC,AD", 2) == build_action_list("A|C,A|D", 2)
