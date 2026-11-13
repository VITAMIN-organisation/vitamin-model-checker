"""Pinned TOL semantics on a two-state cost-bounded timedCGS fixture."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.TCTL.TCTL import (
    model_checking as tctl_model_checking,
)
from model_checker.algorithms.explicit.TOL.TOL import model_checking
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tol_cost_2states.txt"
)


def _states_from_result(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


class TestCostBoundedSemantics:
    """{Jk} operators with non-zero Transition_With_Costs cells (paper ▼ semantics)."""

    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_true"),
        [
            ("p", {"s1"}, False),
            ("q", {"s0"}, True),
            ("{J2}X p", {"s0"}, True),
            ("{J3}X p", {"s0"}, True),
            ("{J5}X p", {"s0"}, True),
            ("{J1}X q", {"s1"}, False),
            ("{J4}X q", {"s1"}, False),
            ("{J2}F p", {"s0", "s1"}, True),
            ("{J3}F p", {"s0", "s1"}, True),
            ("{J5}F p", {"s0", "s1"}, True),
            ("{J5}G p", set(), False),
            ("{J2} q U p", {"s0", "s1"}, True),
            ("{J3} q U p", {"s0", "s1"}, True),
            ("{J3} q R p", set(), False),
            ("{J5} q R p", set(), False),
            ("{J2} q W p", {"s0", "s1"}, True),
            ("{J3} q W p", {"s0", "s1"}, True),
            ("{J5} q W p", {"s0", "s1"}, True),
        ],
    )
    def test_formula_semantics(self, formula, expected_states, initial_true):
        result = model_checking(formula, str(_FIXTURE))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_true}"


class TestGradeZero:
    """`{J0}`: the Demon has no budget but may still disable edges of cost 0."""

    def test_zero_cost_edge_can_be_disabled(self):
        """The Demon cuts the 0:0 edge s0 -> s1 and keeps the cost-5 loop at s0."""
        fixture = str(_FIXTURE.with_name("tol_zero_cost_edge.txt"))
        assert _states_from_result(model_checking("{J0} G !p", fixture)) == {"s0"}
        assert _states_from_result(model_checking("{J0} F p", fixture)) == {"s1"}

    @pytest.mark.parametrize(
        ("tol", "tctl"), [("{J0} F p", "AF p"), ("{J0} G !p", "AG !p")]
    )
    def test_grade_zero_matches_tctl_without_zero_cost_edges(self, tol, tctl):
        """s0 branches over edges of cost 5 and 2; grade 0 cuts neither, as TCTL A."""
        fixture = str(_FIXTURE.with_name("tol_positive_cost_branch.txt"))
        tol_states = _states_from_result(model_checking(tol, fixture))
        tctl_states = _states_from_result(tctl_model_checking(tctl, fixture))
        assert tol_states == tctl_states


def test_syntax_error():
    result = model_checking("{J2}X p (", str(_FIXTURE))
    assert "error" in result
    assert result["error"]["type"] == "syntax"


@pytest.mark.parametrize(
    ("formula", "expected_states", "initial_true"),
    [
        ("true", {"s0", "s1"}, True),
        ("false", set(), False),
        ("#", set(), False),
        ("@", {"s0", "s1"}, True),
        ("x>20", set(), False),
    ],
)
def test_tol_booleans_and_clock_gt(formula, expected_states, initial_true):
    result = model_checking(formula, str(_FIXTURE))
    assert _states_from_result(result) == expected_states
    assert result["initial_state"] == f"Initial state s0: {initial_true}"
