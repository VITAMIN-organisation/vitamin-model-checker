"""Conditions of the LTL rule lists: every connective passed in, and `!` on any atom."""

import pytest

from model_checker.algorithms.explicit.shared.strategies_base import (
    generate_conditions,
    generate_negated_conditions,
)


@pytest.mark.unit
def test_conditions_use_both_connectives():
    """Two atoms of size 3 give `p and q` and `p or q`, not one picked connective."""
    assert set(generate_conditions(["p", "q"], ["and", "or"], 3)) == {
        "p",
        "q",
        "p and q",
        "p or q",
    }


@pytest.mark.unit
def test_negation_can_fall_on_any_atom():
    """`p and !q` is a condition of size 4, as is `!p and q`."""
    assert set(generate_negated_conditions(["p and q"], 4)) == {
        "p and q",
        "!p and q",
        "p and !q",
        "!p and !q",
    }
