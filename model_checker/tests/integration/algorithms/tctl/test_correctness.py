"""TCTL model checking on timedCGS."""

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
_AF_REGRESSION = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_af_regression.txt"
)
_AU_REGRESSION = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_au_regression.txt"
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


@pytest.mark.parametrize(
    ("formula", "expected_locations", "initial_ok"),
    [
        # AF p: s0 is forced to s1 where p holds, so all paths eventually reach p.
        # AG p: only s1 (s0 lacks p even though it reaches s1 next step).
        ("AF p", {"s0", "s1"}, True),
        ("AG p", {"s1"}, False),
        ("EF p", {"s0", "s1"}, True),
        ("EG p", {"s1"}, False),
    ],
)
def test_tctl_af_differs_from_ag(formula, expected_locations, initial_ok):
    result = model_checking(formula, str(_AF_REGRESSION))
    assert _states(result) == expected_locations
    assert _initial_satisfied(result) is initial_ok


@pytest.mark.parametrize(
    ("formula", "expected_locations", "initial_ok"),
    [
        # A[!p U p]: s0 can self-loop forever, so all-paths guarantee fails at s0.
        # E[!p U p]: s0 has the path s0->s1 where !p then p, so both states satisfy.
        ("A (!p) U p", {"s1"}, False),
        ("E (!p) U p", {"s0", "s1"}, True),
        ("A ((!p) U p)", {"s1"}, False),
        ("E ((!p) U p)", {"s0", "s1"}, True),
    ],
)
def test_tctl_au_differs_from_eu(formula, expected_locations, initial_ok):
    result = model_checking(formula, str(_AU_REGRESSION))
    assert _states(result) == expected_locations
    assert _initial_satisfied(result) is initial_ok


def test_syntax_error():
    result = model_checking("EF p (", str(_MINIMAL))
    assert "error" in result or "Syntax" in result.get("res", "")
