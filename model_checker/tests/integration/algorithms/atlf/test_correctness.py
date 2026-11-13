"""ATLF on atlf_2agents_4states_fuzzy.txt, every value worked out by hand.

s0 -AC-> s1, s0 -AD-> s2, s1 -BC-> s1, s1 -BD-> s3, s2 and s3 loop. Agent 1 has one
action per state, so agent 2 alone picks the successor. p is 0 at s0, 0.2 at s1,
0.7 at s2 and 0.4 at s3.
"""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import model_checking as atl_checking
from model_checker.algorithms.explicit.ATLF.ATLF import model_checking
from model_checker.utils.literals import parse_tuple_list_literal

_MODEL = "fuzzyCGS/ATLF/atlf_2agents_4states_fuzzy.txt"

_CASES = [
    # agent 1 cannot choose, so it gets the worse successor: min(0.2, 0.7) at s0
    ("<1>X p", {"s0": 0.2, "s1": 0.2, "s2": 0.7, "s3": 0.4}),
    # agent 2 picks the better successor: s2 from s0, s3 from s1
    ("<2>X p", {"s0": 0.7, "s1": 0.4, "s2": 0.7, "s3": 0.4}),
    # agent 2 can keep the play in s1, so from s0 agent 1 is sure of 0.2 only
    ("<1>F p", {"s0": 0.2, "s1": 0.2, "s2": 0.7, "s3": 0.4}),
    ("<1>G p", {"s0": 0.0, "s1": 0.2, "s2": 0.7, "s3": 0.4}),
    # 1 - p, printed without float noise (1 - 0.7 is 0.30000000000000004)
    ("!p", {"s0": 1.0, "s1": 0.8, "s2": 0.3, "s3": 0.6}),
]


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.parametrize(("formula", "expected"), _CASES)
def test_value_per_state_matches_the_hand_computed_one(
    test_data_dir, formula, expected
):
    result = model_checking(formula, str(test_data_dir / _MODEL))
    assert "error" not in result, result
    values = dict(parse_tuple_list_literal(result["res"].removeprefix("Result: ")))
    assert values == expected
    assert result["initial_state"] == f"Initial state s0: {expected['s0']}"


@pytest.mark.integration
@pytest.mark.model_checking
def test_atl_refuses_fuzzy_labels(test_data_dir):
    """ATL reads a CGS, where only 0 and 1 are labels."""
    result = atl_checking("<1>X p", str(test_data_dir / _MODEL))
    assert "Invalid labelling matrix value: '0.2'" in str(result.get("error")), result
