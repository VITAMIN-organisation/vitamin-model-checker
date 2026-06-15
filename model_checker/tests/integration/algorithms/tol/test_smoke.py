"""Smoke and correctness tests for TOL model checking."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.TOL.TOL import model_checking
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_tol_minimal.txt"
)


def _states(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


@pytest.mark.parametrize(
    ("formula", "expected_states", "initial_true"),
    [
        ("p", {"s0"}, True),
        ("{J5}F p", {"s0"}, True),
        ("{J5}G p", {"s0"}, True),
        ("{J5}X p", {"s0"}, True),
    ],
)
def test_formula_semantics(formula, expected_states, initial_true):
    result = model_checking(formula, str(_FIXTURE))
    assert _states(result) == expected_states
    assert result["initial_state"] == f"Initial state s0: {initial_true}"


def test_syntax_error():
    result = model_checking("{J5}F p (", str(_FIXTURE))
    assert "error" in result or "Syntax" in result.get("res", "")
