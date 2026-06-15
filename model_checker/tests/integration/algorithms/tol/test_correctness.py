"""Pinned TOL semantics on a two-state cost-bounded timedCGS fixture."""

from pathlib import Path

import pytest

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
    """{Jk} operators with non-zero Transition_With_Costs cells."""

    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_true"),
        [
            ("p", {"s1"}, False),
            ("q", {"s0"}, True),
            ("{J2}X p", set(), False),
            ("{J3}X p", {"s0"}, True),
            ("{J5}X p", {"s0"}, True),
            ("{J1}X q", set(), False),
            ("{J4}X q", {"s1"}, False),
            ("{J2}F p", {"s1"}, False),
            ("{J3}F p", {"s0", "s1"}, True),
            ("{J5}F p", {"s0", "s1"}, True),
            ("{J5}G p", set(), False),
            ("{J2} q U p", {"s1"}, False),
            ("{J3} q U p", {"s0", "s1"}, True),
        ],
    )
    def test_formula_semantics(self, formula, expected_states, initial_true):
        result = model_checking(formula, str(_FIXTURE))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_true}"
