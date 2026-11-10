"""NatATL with recall: the strategies of complexity exactly k, one guarded rule list per agent.

A rule's complexity is the number of words in its condition, plus one for `!`; so
`p` costs 1, `!p` 2 and `p && q` 3. A strategy's rules use distinct actions. The
solver asks for k = 1, 2, ... in turn, so "at most k" is the union of those calls.
"""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.strategy_generation import (
    generate_guarded_action_pairs,
    generate_strategies,
    is_duplicate,
)


def _rules(cartesian_products, k, agents=(1,)):
    """Each yielded profile as a list of rule lists, one per agent."""
    profiles = generate_strategies(cartesian_products, k, list(agents), False)
    return [
        [agent["condition_action_pairs"] for agent in profile] for profile in profiles
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("k", "rules"),
    [
        (1, [[[("p", "a")]], [[("q", "b")]]]),
        (2, [[[("p", "a"), ("q", "b")]]]),
        (3, []),
    ],
)
def test_strategies_have_exactly_the_requested_complexity(k, rules):
    """With rules p->a and q->b: one rule each at k=1, both at k=2, none at k=3."""
    assert _rules({"actions_agent1": [("p", "a"), ("q", "b")]}, k) == rules


@pytest.mark.unit
@pytest.mark.parametrize(
    ("condition", "k", "rules"),
    [
        ("!p", 1, [[[("q", "b")]]]),
        ("!p", 2, [[[("!p", "a")]]]),
        ("p && q", 2, []),
        ("p && q", 3, [[[("p && q", "a")]]]),
    ],
)
def test_negation_and_conjunction_add_to_the_complexity(condition, k, rules):
    """`!p` costs 2 and `p && q` costs 3, so they first appear at those bounds."""
    assert _rules({"actions_agent1": [(condition, "a"), ("q", "b")]}, k) == rules


@pytest.mark.unit
def test_two_rules_with_the_same_action_are_not_one_strategy():
    """p->a with q->a repeats the action, so only pairs with b are kept at k=2."""
    rules = _rules({"actions_agent1": [("p", "a"), ("q", "a"), ("r", "b")]}, 2)
    assert rules == [[[("p", "a"), ("r", "b")]], [[("q", "a"), ("r", "b")]]]


@pytest.mark.unit
def test_profiles_combine_one_strategy_per_agent():
    """Two agents with one rule each give one joint profile."""
    rules = _rules(
        {"actions_agent1": [("p", "a")], "actions_agent2": [("q", "c")]},
        1,
        agents=(1, 2),
    )
    assert rules == [[[("p", "a")], [("q", "c")]]]


@pytest.mark.unit
def test_nothing_is_generated_once_a_solution_is_found():
    """The solver passes found_solution=True to stop the search."""
    assert generate_strategies({"actions_agent1": [("p", "a")]}, 1, [1], True) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("new_pairs", "duplicate"),
    [
        ([("p", "a"), ("q", "b")], True),
        ([("q", "b"), ("p", "a")], False),
        ([("p", "c")], False),
    ],
)
def test_duplicate_means_the_same_rules_in_the_same_order(new_pairs, duplicate):
    """Rule order matters: the first matching rule decides the action."""
    existing = [{"condition_action_pairs": [("p", "a"), ("q", "b")]}]
    assert is_duplicate(existing, {"condition_action_pairs": new_pairs}) is duplicate


@pytest.mark.unit
def test_guarded_pairs_are_every_condition_with_every_action_of_each_agent():
    """Agent 1 has a and b, agent 2 has c; conditions p and q."""
    assert generate_guarded_action_pairs(["p", "q"], [["a", "b"], ["c"]]) == {
        "actions_agent1": [("p", "a"), ("p", "b"), ("q", "a"), ("q", "b")],
        "actions_agent2": [("p", "c"), ("q", "c")],
    }
