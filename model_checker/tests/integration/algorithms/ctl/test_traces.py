"""CTL traces: a witness for a true E-operator root, a counterexample for a false A-operator root.

The expected traces are worked out by hand on atl_2agents_4states_simple.txt:
s0:{p} s1:{q} s2:{} s3:{p,q}, with the edges in _EDGES. A lasso lists each state
once; after its last state the path steps back to states[cycle_start_index].
"""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import model_checking

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
    ("formula", "holds", "states", "cycle_start"),
    [
        # q = {s1,s3}; s1 is the only successor of s0 in q.
        ("EX q", True, ["s0", "s1"], None),
        # s2 is the only successor of s0 outside q.
        ("AX q", False, ["s0", "s2"], None),
        # !p && !q = {s2}, one step from s0.
        ("EF (!p && !q)", True, ["s0", "s2"], None),
        # s0 is in p, so the path ends where it starts.
        ("EF p", True, ["s0"], None),
        # s2 is the only state outside p || q.
        ("AG (p || q)", False, ["s0", "s2"], None),
        # p = {s0,s3}; s1 is the only successor of s0 in q.
        ("E[p U q]", True, ["s0", "s1"], None),
        # EG (p || q) = {s0,s1,s3}; the only path inside it is s0 s1 s3 s3 ...
        ("EG (p || q)", True, ["s0", "s1", "s3"], 2),
        # AF (!p && !q) = {s2}; the path s0 s1 s3 s3 ... never reaches s2.
        ("AF (!p && !q)", False, ["s0", "s1", "s3"], 2),
        # s2 has neither p nor q and is reached from s0 before any q state.
        ("A[p U q]", False, ["s0", "s2"], None),
        # No state has neither side; s0 s1 s3 s3 ... stays in p || q without s2.
        ("A[(p || q) U (!p && !q)]", False, ["s0", "s1", "s3"], 2),
    ],
)
def test_trace_shows_why_the_root_operator_holds_or_fails(
    cgs_simple_parser, formula, holds, states, cycle_start
):
    """The path ends in, or the lasso stays in, the states the operator needs."""
    result = model_checking(formula, cgs_simple_parser.filename, generate_trace=True)
    assert result["initial_state"] == f"Initial state s0: {holds}"
    trace = result["trace"]
    assert trace["type"] == ("witness" if holds else "counterexample")
    assert trace["states"] == states
    assert trace["cycle_start_index"] == cycle_start
    assert trace["length"] == len(states)
    steps = list(zip(states, states[1:], strict=False))
    if cycle_start is not None:
        steps.append((states[-1], states[cycle_start]))
    assert all(step in _EDGES for step in steps)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "holds"),
    [
        ("EG p", False),
        ("AF q", True),
        ("!EF q", False),
        ("(EX q) && (EG (p || q))", True),
    ],
    ids=["false_E_operator", "true_A_operator", "negated_root", "conjunction_root"],
)
def test_no_trace_where_one_path_cannot_show_the_verdict(
    cgs_simple_parser, formula, holds
):
    """A false E-operator, a true A-operator and a boolean root give trace None."""
    result = model_checking(formula, cgs_simple_parser.filename, generate_trace=True)
    assert result["initial_state"] == f"Initial state s0: {holds}"
    assert result["trace"] is None


@pytest.mark.integration
def test_res_with_a_trace_is_the_sorted_tuple_of_the_plain_result(cgs_simple_parser):
    """Every state has a successor in q, so EX q holds everywhere, in both forms."""
    plain = model_checking("EX q", cgs_simple_parser.filename)
    traced = model_checking("EX q", cgs_simple_parser.filename, generate_trace=True)
    assert traced["res"] == plain["res"] == "Result: ('s0', 's1', 's2', 's3')"


@pytest.mark.integration
def test_no_trace_unless_asked(cgs_simple_parser):
    """The default result has only the verdict fields."""
    result = model_checking("EX q", cgs_simple_parser.filename)
    assert "trace" not in result
