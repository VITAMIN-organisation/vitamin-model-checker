"""NatATL Recall patterns: their size, and which actions a rule may play."""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.patterns import (
    ANY_HISTORY,
    Pattern,
    true_letter,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategies import valid_rules
from model_checker.algorithms.explicit.NatATL.Recall.validity import (
    last_states,
    successors,
)
from model_checker.algorithms.explicit.shared.natural_strategies import (
    Condition,
    available_actions,
    enumerate_conditions,
    parse_rows,
)
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


def _model(temp_file, transitions, labelling, prop_names, num_agents):
    content = build_cgs_model_content(
        transitions=transitions,
        state_names=[f"s{i}" for i in range(len(transitions))],
        initial_state="s0",
        labelling=labelling,
        num_agents=num_agents,
        prop_names=prop_names,
    )
    return load_cgs_from_content(temp_file, content)


def _actions_of(cgs, pattern, agent):
    """The actions the solver accepts for a rule with this pattern."""
    rows = parse_rows(cgs)
    ends = {pattern: last_states(pattern, successors(cgs.states, rows))}
    rules = valid_rules(ends, available_actions(cgs.states, rows, agent))
    return frozenset(action for _, action in rules)


def _atoms(cgs):
    return {c.text: c for c in enumerate_conditions(cgs, 1)}


@pytest.mark.unit
def test_pattern_size_skips_leading_true_star():
    """The RoboCup recall strategy in docs/algorithms/natatl.md has size 11."""
    top = true_letter([])
    moved = Condition("moved", frozenset({"q1"}), 1)
    stayed = Condition("stayed", frozenset({"q2"}), 1)
    rules = [
        Pattern(((top, False),)),
        Pattern(((top, False), (top, False))),
        Pattern(((moved, False), (top, False)), any_prefix=True),
        Pattern(((stayed, False), (top, False)), any_prefix=True),
        ANY_HISTORY,
    ]
    assert sum(rule.size for rule in rules) == 11


@pytest.mark.unit
def test_plain_condition_rule_needs_its_action_where_the_condition_holds(temp_file):
    """In m1 only s1 (q) lets agent 1 play b; r holds at s2, where it can only idle."""
    cgs = _model(
        temp_file,
        [["0", "II", "0"], ["0", "II", "bI"], ["0", "0", "II"]],
        [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        ["p", "q", "r"],
        2,
    )
    atoms = _atoms(cgs)
    assert "b" not in _actions_of(cgs, Pattern(((atoms["r"], False),)), 1)
    assert "b" in _actions_of(cgs, Pattern(((atoms["q"], False),)), 1)


@pytest.mark.unit
def test_rule_is_invalid_where_a_long_matching_history_ends_without_its_action(
    temp_file,
):
    """Every history matching a . b* . f ends at s5, at least six states after s0,
    and B is not available at s5."""
    cgs = _model(
        temp_file,
        [
            ["I", "B", "0", "0", "0", "0"],
            ["0", "I", "B", "0", "0", "0"],
            ["0", "0", "I", "B", "0", "0"],
            ["0", "0", "0", "I", "B", "0"],
            ["0", "0", "0", "0", "I", "B"],
            ["0", "0", "0", "0", "0", "I"],
        ],
        [["1", "0", "0"]] + [["0", "1", "0"]] * 4 + [["0", "0", "1"]],
        ["a", "b", "f"],
        1,
    )
    atoms = _atoms(cgs)
    pattern = Pattern(((atoms["a"], False), (atoms["b"], True), (atoms["f"], False)))
    assert _actions_of(cgs, pattern, 1) == frozenset({"IDLE"})
