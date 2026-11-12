"""costCGS cost lines: `<joint> <state>$<costs>` gives each agent's cost of a joint action at a state."""

import re

import pytest

from model_checker.parsers.game_structures.cost_cgs import cost_cgs_parser
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS


@pytest.mark.unit
@pytest.mark.parametrize(
    ("line", "split", "message"),
    [
        ("I*", False, "Malformed cost line"),
        ("I* s0$", False, "Malformed cost entry"),
        ("I* s0$1:x", False, "Invalid cost value"),
        ("I* s0$1:x,y", True, "Invalid cost value"),
    ],
)
def test_malformed_cost_line_is_refused(line, split, message):
    """No state, no cost after `$`, or a cost that is not a number."""
    with pytest.raises(ValueError, match=message):
        cost_cgs_parser.parse_cost_line(line, CostCGS(), parse_split=split)


@pytest.mark.unit
def test_extra_token_on_cost_line_is_refused():
    """`I* s0$1 s1$2` has a third token (a missing `;`); it must not be dropped."""
    with pytest.raises(ValueError, match=r"Unexpected token 's1\$2'.*I\* s0\$1 s1\$2"):
        cost_cgs_parser.parse_cost_line("I* s0$1 s1$2", CostCGS(), parse_split=False)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("line", "split", "value"),
    [("I* s0$1:-2", False, "-2"), ("I* s0$1,-3:4,5", True, "-3")],
)
def test_negative_cost_is_refused(line, split, value):
    """A cost is a non-negative amount of resource; the error names the value and the line."""
    with pytest.raises(ValueError, match=f"{re.escape(line)}.*Negative cost {value}"):
        cost_cgs_parser.parse_cost_line(line, CostCGS(), parse_split=split)


@pytest.mark.unit
def test_cost_lookup_accepts_compact_and_piped_joints():
    """`AAC` and `A|A|C` name the same joint, so both find the cost written for AAC."""
    instance = CostCGS()
    instance.number_of_agents = 3
    cost_cgs_parser.parse_cost_line("AAC s0$1,1,1", instance, parse_split=True)
    cost_cgs_parser.parse_cost_line("*** s1$2:2", instance, parse_split=False)
    cost_cgs_parser.normalize_cost_action_keys(instance)

    assert instance.get_cost_for_action("AAC", "s0") == [[1, 1, 1]]
    assert instance.get_cost_for_action("A|A|C", "s0") == [[1, 1, 1]]
    assert instance.get_cost_for_action("***", "s1") == [2, 2]
    assert instance.get_cost_for_action("*|*|*", "s1") == [2, 2]


@pytest.mark.unit
def test_cost_lookup_accepts_non_letter_action_tokens():
    """A compact joint may use symbols such as `^`; it normalizes like letters."""
    instance = CostCGS()
    instance.number_of_agents = 3
    cost_cgs_parser.parse_cost_line("AA^ s0$1:1", instance, parse_split=False)
    cost_cgs_parser.normalize_cost_action_keys(instance)
    assert instance.get_cost_for_action("AA^", "s0") == [1, 1]
    assert instance.get_cost_for_action("A|A|^", "s0") == [1, 1]
