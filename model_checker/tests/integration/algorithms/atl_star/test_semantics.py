"""ATL* end to end: path formulas under a coalition that ATL cannot write, on plain CGS files.

The four-state model is atl_2agents_4states_simple.txt (edges and labels in
integration/algorithms/atl/test_semantics.py). Needs Spot.
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL_STAR.ATL_STAR import model_checking
from model_checker.tests.helpers.model_helpers import extract_states_from_result
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content

pytestmark = pytest.mark.atl_star

_ALL = {"s0", "s1", "s2", "s3"}


def _states(formula, path):
    result = model_checking(formula, path)
    assert "error" not in result, result
    return extract_states_from_result(result)


@pytest.fixture
def first_agent_decides(temp_file):
    """From s0 agent 1's i stays and a moves to s1 (goal), whatever agent 2 plays; s1 loops."""
    return temp_file(
        build_cgs_model_content(
            transitions=[["iI,iO", "aI,aO"], ["0", "*"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            prop_names=["goal"],
            labelling=[["0"], ["1"]],
            num_agents=2,
        )
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("<<1>> X goal", {"s0", "s1"}),
        ("<<2>> X goal", {"s1"}),  # agent 2 cannot move s0 to s1
        # a coalition nested inside a path formula
        ("<<1>> F (<<2>> G goal)", {"s0", "s1"}),
    ],
)
def test_who_controls_the_move(first_agent_decides, formula, expected):
    """Only agent 1's letter picks the successor of s0."""
    assert _states(formula, first_agent_decides) == expected


@pytest.mark.integration
def test_until_over_two_steps(temp_file):
    """mid holds at s0 and s1, goal only at s2: mid U goal holds on the whole chain."""
    path = temp_file(
        build_cgs_model_content(
            transitions=[["0", "a", "0"], ["0", "0", "b"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            prop_names=["mid", "goal"],
            labelling=[["1", "0"], ["1", "0"], ["0", "1"]],
            num_agents=1,
        )
    )
    assert _states("<<1>> (mid U goal)", path) == {"s0", "s1", "s2"}


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("<<1,2>> F (p && q)", _ALL),  # every path ends in s3
        ("<<1>> F (p && q)", _ALL),
        ("<<1,2>> (X q && X X p)", _ALL),  # s0 -AC-> s1 -AC-> s3
        ("<<1>> (X q && X X p)", {"s2", "s3"}),  # at s1 agent 2 can pick D and reach s2
        ("<<2>> (X q && X X p)", {"s1", "s2", "s3"}),  # at s1 agent 2 plays C to s3
        # agent 2 can always steer into s2 first
        ("<<1>> (F q && G !(!p && !q))", {"s3"}),
    ],
)
def test_path_formulas_on_the_four_state_model(cgs_simple_parser, formula, expected):
    """Conjunctions of temporal goals under one coalition, worked out from the edges."""
    assert _states(formula, cgs_simple_parser.filename) == expected
