"""Pinned TCTL semantics on the minimal timedCGS fixture."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.TCTL.TCTL import model_checking
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_tol_minimal.txt"
)


def _states_from_result(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


class TestTemporalOperators:
    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_satisfied"),
        [
            ("AF p", {"s0"}, True),
            ("EG p", {"s0"}, True),
            ("EF x<=1", {"s0"}, True),
            ("AG x<=1", {"s0"}, True),
            ("E p U q", set(), False),
            ("A p U q", set(), False),
        ],
    )
    def test_formula_semantics(self, formula, expected_states, initial_satisfied):
        result = model_checking(formula, str(_FIXTURE))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"


class TestClockGuards:
    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_satisfied"),
        [
            ("EF (p : x<=1)", {"s0"}, True),
            ("AG (p : x<=1)", {"s0"}, True),
            ("E (p : x<=1) U p", {"s0"}, True),
        ],
    )
    def test_clock_guarded_subformulas(
        self, formula, expected_states, initial_satisfied
    ):
        result = model_checking(formula, str(_FIXTURE))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"
