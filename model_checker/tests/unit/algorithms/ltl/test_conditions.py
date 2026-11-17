"""Conditions of the LTL rule lists: every connective passed in, and `!` on any atom."""

import pytest

from model_checker.algorithms.explicit.shared.strategies_base import (
    condition_size,
    generate_conditions,
    generate_negated_conditions,
    generate_strategies,
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
@pytest.mark.parametrize(
    ("condition", "size"),
    [("p", 1), ("!p", 2), ("p and !q", 4), ("!p and !q", 5), ("!p or !q or !r", 8)],
)
def test_each_negation_counts_one(condition, size):
    """The size is the words plus one per `!`, as in NatATL."""
    assert condition_size(condition) == size


@pytest.mark.unit
def test_negation_can_fall_on_any_atom():
    """`p and !q` is a condition of size 4, as is `!p and q`; `!p and !q` needs 5."""
    assert set(generate_negated_conditions(["p and q"], 4)) == {
        "p and q",
        "!p and q",
        "p and !q",
    }
    assert "!p and !q" in set(generate_negated_conditions(["p and q"], 5))


@pytest.mark.unit
@pytest.mark.parametrize(("bound", "count"), [(4, 0), (5, 1)])
def test_a_rule_with_two_negations_fits_only_from_size_5(bound, count):
    """The rule `!p and !q -> A` has size 5, so strategy generation finds it at k = 5."""
    pairs = {"agent1": [("!p and !q", "A")]}
    assert len(list(generate_strategies(pairs, bound, [1], False))) == count
