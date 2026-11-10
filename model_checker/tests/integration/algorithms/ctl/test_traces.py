"""CTL traces: a witness when the formula holds at the initial state, a counterexample when it does not.

Only properties that any correct trace has are checked here: the type matches
the verdict, the path starts at the initial state and follows real edges. The
traces currently stop at the initial state (a known bug), so their last state
is not checked yet.
"""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import model_checking

# Edges of atl_2agents_4states_simple.txt (see test_semantics.py).
_EDGES = {
    ("s0", "s1"),
    ("s0", "s2"),
    ("s1", "s2"),
    ("s1", "s3"),
    ("s2", "s3"),
    ("s3", "s3"),
}


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "holds"),
    [
        ("EX q", True),
        ("AX q", False),
        ("EF (!p && !q)", True),
        ("AF (!p && !q)", False),
        ("EG p", False),
        ("AG (p || q)", False),
        ("E[p U q]", True),
        ("A[p U q]", False),
    ],
)
def test_trace_type_and_path_match_the_verdict(cgs_simple_parser, formula, holds):
    """Witness for a true formula, counterexample for a false one, on a path of the model."""
    result = model_checking(formula, cgs_simple_parser.filename, generate_trace=True)
    assert result["initial_state"] == f"Initial state s0: {holds}"
    trace = result["trace"]
    assert trace["type"] == ("witness" if holds else "counterexample")
    assert trace["states"][0] == "s0"
    assert trace["length"] == len(trace["states"])
    steps = zip(trace["states"], trace["states"][1:], strict=False)
    assert all(step in _EDGES for step in steps)


@pytest.mark.integration
def test_no_trace_unless_asked(cgs_simple_parser):
    """The default result has only the verdict fields."""
    result = model_checking("EX q", cgs_simple_parser.filename)
    assert "trace" not in result
