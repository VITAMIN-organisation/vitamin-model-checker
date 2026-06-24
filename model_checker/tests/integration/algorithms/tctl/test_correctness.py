"""TCTL model checking on timedCGS (TIGER Ch. 6 rsat semantics)."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.TCTL.TCTL import model_checking
from model_checker.utils.literals import parse_state_set_literal

_MINIMAL = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_tol_minimal.txt"
)


def _states(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


def _initial_satisfied(result):
    assert "error" not in result
    return result["initial_state"].endswith(": True")


@pytest.mark.parametrize(
    ("formula", "expected_locations", "initial_ok"),
    [
        ("p", {"s0"}, True),
        ("EF p", {"s0"}, True),
        ("AF p", {"s0"}, True),
        ("EG p", {"s0"}, True),
        ("AG p", {"s0"}, True),
        ("EF x<=1", {"s0"}, True),
        ("AG x<=1", {"s0"}, True),
        ("E p U q", set(), False),
        ("A p U q", set(), False),
        ("E p U p", {"s0"}, True),
        ("A p U p", {"s0"}, True),
        ("E (p U p)", {"s0"}, True),
        ("A (p U p)", {"s0"}, True),
    ],
)
def test_tctl_semantics(formula, expected_locations, initial_ok):
    result = model_checking(formula, str(_MINIMAL))
    assert _states(result) == expected_locations
    assert _initial_satisfied(result) is initial_ok


@pytest.mark.parametrize(
    ("formula", "expected_locations", "initial_ok"),
    [
        ("EF (p : x<=1)", {"s0"}, True),
        ("AG (p : x<=1)", {"s0"}, True),
        ("E (p : x<=1) U p", {"s0"}, True),
        ("j.p", {"s0"}, True),
        ("E (j<=2) U p", {"s0"}, True),
    ],
)
def test_tctl_clock_guards_and_freeze(formula, expected_locations, initial_ok):
    result = model_checking(formula, str(_MINIMAL))
    assert _states(result) == expected_locations
    assert _initial_satisfied(result) is initial_ok


def test_syntax_error():
    result = model_checking("EF p (", str(_MINIMAL))
    assert "error" in result or "Syntax" in result.get("res", "")
