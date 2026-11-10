"""ATL and ATLF on atl_2agents_4states_simple.txt, every expected set worked out by hand.

Cells are joint actions, agent 1's letter first: s0 -AC,AD-> s1, s0 -BC,BD-> s2,
s1 -AD,BD-> s2, s1 -AC,BC-> s3, s2 -AD,BC-> s3, s3 -*-> s3. p holds at s0 and s3,
q at s1 and s3. At s2 only AD and BC exist, so every move there reaches s3.
"""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import model_checking
from model_checker.algorithms.explicit.ATLF.ATLF import (
    model_checking as atlf_model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content
from model_checker.utils.literals import parse_tuple_list_literal

_ALL = {"s0", "s1", "s2", "s3"}

_CASES = [
    # at s0 agent 1 plays A to reach s1; at s1 agent 2 can pick s2
    ("<1>X q", {"s0", "s2", "s3"}),
    # at s0 agent 1 decides between s1 and s2
    ("<2>X q", {"s1", "s2", "s3"}),
    ("<1,2>X q", _ALL),  # together they pick any listed joint action
    ("!<1>X q", {"s1"}),
    ("<1>F q", _ALL),
    ("<1>G p", {"s3"}),  # s0 must leave p at once
    # agent 1 can stay in !q at s0 -> s2, but s2 must go to s3
    ("<1>G !q", set()),
    # agent 1 plays B at s0; at s1 agent 2 can avoid s2
    ("<1>F (!p && !q)", {"s0", "s2"}),
    # agent 2 plays D at s1, and C at s0 lands in s1 or s2
    ("<2>F (!p && !q)", {"s0", "s1", "s2"}),
    # agent 1 leaves s0 for s1 while p holds
    ("<1>(p U q)", {"s0", "s1", "s3"}),
    ("<2>(p U q)", {"s1", "s3"}),
    # nested coalitions: <2>X q holds at s1, which agent 1 reaches
    ("<1>F (<2>X q)", _ALL),
]


def _atl(formula, path):
    result = model_checking(formula, path)
    assert "error" not in result, result
    return extract_states_from_result(result)


@pytest.mark.integration
@pytest.mark.parametrize(("formula", "expected"), _CASES)
def test_formula_on_the_four_state_model(cgs_simple_parser, formula, expected):
    """Each set follows from who chooses which successor, as in the module docstring."""
    assert _atl(formula, cgs_simple_parser.filename) == expected


@pytest.mark.integration
@pytest.mark.parametrize(
    "transitions",
    [
        [["0", "AC,BC", "AD,BD"], ["0", "II", "0"], ["0", "0", "II"]],
        [["0", "A|C,B|C", "A|D,B|D"], ["0", "I|I", "0"], ["0", "0", "I|I"]],
    ],
    ids=["compact", "piped"],
)
def test_compact_and_piped_cells_give_the_same_answer(temp_file, transitions):
    """Agent 2's C or D picks s1 (p) or s2; agent 1's letter does not matter."""
    path = temp_file(
        build_cgs_model_content(
            transitions=transitions,
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            prop_names=["p"],
            labelling=[["0"], ["1"], ["0"]],
            num_agents=2,
        )
    )
    assert _atl("<1>X p", path) == {"s1"}
    assert _atl("<2>X p", path) == {"s0", "s1"}
    assert _atl("<1,2>X p", path) == {"s0", "s1"}


@pytest.mark.integration
@pytest.mark.parametrize(("formula", "expected"), _CASES)
def test_atlf_on_binary_labels_is_one_exactly_where_atl_holds(
    cgs_simple_parser, formula, expected
):
    """With 0/1 labels the real value at a state is 1.0 if the ATL formula holds there and 0.0 if not."""
    result = atlf_model_checking(formula, cgs_simple_parser.filename)
    assert "error" not in result, result
    values = dict(parse_tuple_list_literal(result["res"].removeprefix("Result: ")))
    assert values == {state: 1.0 if state in expected else 0.0 for state in _ALL}
    assert result["initial_state"] == f"Initial state s0: {values['s0']}"
