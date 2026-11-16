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
_ZENO_CYCLE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_zeno_cycle.txt"
)
_RESET_CYCLE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_reset_cycle.txt"
)
_INVARIANT10 = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "timedCGS"
    / "tctl_tol_invariant10.txt"
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
        ("AG x<=1", set(), False),
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
        ("AG (p : x<=1)", set(), False),
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
    ("formula", "initial_ok"),
    [
        ("AG (p : x<=3)", False),
        ("EF !(p : x<=3)", True),
        ("EF (p : x>5)", True),
        ("AG !(p : x>5)", False),
        ("p : x<=3", True),
        ("AG (p && x<=3)", False),
        ("AG (x<=3)", False),
        ("j.AG (p : j<=3)", False),
        # Time passes through 3<x<5, where neither side holds.
        ("E (x<=3 U x>=5)", False),
        ("E (x<=3 U x>3)", True),
    ],
)
def test_tctl_clock_guard_holds_for_every_clock_value(formula, initial_ok):
    """Time at s0 runs to x=10, so a guard such as x<=3 fails later on every path."""
    result = model_checking(formula, str(_INVARIANT10))
    assert _initial_satisfied(result) is initial_ok


@pytest.mark.parametrize(
    ("formula", "initial_ok"),
    [
        ("j.EF (j>=2)", True),
        ("EF (x>8 && j.EF (j>=2))", False),
        ("AG j.EF (j>=2)", False),
        ("EF (x>=5 && j.AG (j<=5))", True),
        # At x=6, j runs to 4 and stops.
        ("EF (x>=5 && j.AG (j<=4))", True),
        ("EF (x>8 && j.(j<=0))", True),
        ("AG j.(j<=0)", True),
        ("j.AG (j<=9)", False),
    ],
)
def test_tctl_freeze_resets_its_clock_where_it_stands(formula, initial_ok):
    """After x>8, time at s0 cannot advance by 2, so j.EF (j>=2) fails there."""
    result = model_checking(formula, str(_INVARIANT10))
    assert _initial_satisfied(result) is initial_ok


def test_tctl_freeze_on_a_model_clock_is_a_semantic_error():
    """A freeze binds a formula clock; the model's x may not be reset by the formula."""
    result = model_checking("x.EF (x>=2)", str(_INVARIANT10))
    assert result["error"]["type"] == "semantic"
    assert "'x'" in result["error"]["message"]


def test_tctl_res_lists_only_locations_reached_from_the_start():
    """A formula clock starts at 0 with x, so x>8 && j<=0 holds in no reached region."""
    result = model_checking("x>8 && j<=0 && j.p", str(_INVARIANT10))
    assert _states(result) == set()
    assert _initial_satisfied(result) is False


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
    assert "error" in result
    assert result["error"]["type"] == "syntax"


@pytest.mark.parametrize(
    ("formula", "expected_locations", "initial_ok"),
    [
        ("true", {"s0"}, True),
        ("false", set(), False),
        ("x>5", set(), False),
        ("forall G p", {"s0"}, True),
        ("exist F p", {"s0"}, True),
    ],
)
def test_tctl_booleans_clock_gt_and_word_quantifiers(
    formula, expected_locations, initial_ok
):
    result = model_checking(formula, str(_MINIMAL))
    assert _states(result) == expected_locations
    assert _initial_satisfied(result) is initial_ok


def test_tctl_zeno_cycle():
    # Model has x<=5 invariant on self-loop but no reset.
    # TCTL semantics (without strong non-Zeno requirements) allows infinite 0-time transitions.
    # Therefore EG p is true.
    result = model_checking("EG p", str(_ZENO_CYCLE))
    assert _states(result) == {"s0"}
    assert _initial_satisfied(result) is True


def test_tctl_reset_enables_cycle():
    # Model has x<=5 invariant on self-loop AND resets x=0.
    # Infinite path is possible. EG p must be true.
    result = model_checking("EG p", str(_RESET_CYCLE))
    assert _states(result) == {"s0"}
    assert _initial_satisfied(result) is True
