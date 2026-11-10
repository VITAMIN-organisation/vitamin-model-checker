"""NatATL coalitions carry a strategy-complexity bound: `<{A}, k>`."""

import pytest

from model_checker.parsers.formulas.NatATL.parser import NatATLParser


@pytest.mark.unit
def test_capacity_prefix_keeps_agents_and_bound_in_the_tree():
    """`<{1,2}, 5>F p` becomes the node `<{1,2},5>F` over p."""
    assert NatATLParser().parse("<{1,2}, 5>F p", n_agent=2) == ("<{1,2},5>F", "p")


@pytest.mark.unit
def test_atl_coalition_without_a_bound_is_rejected():
    """`<1,2>F p` has no complexity bound, so it is ATL, not NatATL."""
    assert NatATLParser().parse("<1,2>F p", n_agent=2) is None


@pytest.mark.unit
def test_bound_below_one_is_rejected():
    """k = 0 allows no strategy at all; the smallest bound is 1."""
    parser = NatATLParser()
    assert parser.parse("<{1}, 0>F p", n_agent=2) is None
    assert "Invalid bound 0: must be at least 1" in parser.errors[0]
    assert NatATLParser().parse("<{1}, 1>F p", n_agent=2) is not None
