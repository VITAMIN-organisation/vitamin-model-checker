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
            # Time may stand still at s0, so no budget forces the step to s1.
            ("{J2}F p", {"s1"}, False),
            ("{J3}F p", {"s1"}, False),
            ("{J5}F p", {"s1"}, False),
            ("{J5}G p", set(), False),
            ("{J2} q U p", {"s1"}, False),
            ("{J3} q U p", {"s1"}, False),
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


@pytest.mark.parametrize("formula", ["{J1}G (p : x<=3)", "{J1}(x<=3 U x>=5)"])
def test_demon_cannot_stop_time(formula):
    """Time at s0 runs past x=3, through 3<x<5, and the Demon can only disable edges."""
    fixture = str(_FIXTURE.with_name("tctl_tol_invariant10.txt"))
    result = model_checking(formula, fixture)
    assert result["initial_state"] == "Initial state s0: False"


@pytest.mark.parametrize(
    ("formula", "initial_true"),
    [
        ("{J1}G j.(j<=0)", True),
        ("{J1}G (x>8 -> j.{J1}G (j<=2))", True),
        # From x=8.5, j runs to 1.5 before time stops at x=10.
        ("{J1}G (x>8 -> j.{J1}G (j<=1))", False),
    ],
)
def test_freeze_resets_its_clock_where_it_stands(formula, initial_true):
    """After x>8, time at s0 advances by less than 2, and a freeze counts from there."""
    fixture = str(_FIXTURE.with_name("tctl_tol_invariant10.txt"))
    result = model_checking(formula, fixture)
    assert result["initial_state"] == f"Initial state s0: {initial_true}"


def test_freeze_on_a_model_clock_is_a_semantic_error():
    """A freeze binds a formula clock; the model's x may not be reset by the formula."""
    fixture = str(_FIXTURE.with_name("tctl_tol_invariant10.txt"))
    result = model_checking("{J1}F x.(p : x<5)", fixture)
    assert result["error"]["type"] == "semantic"
    assert "'x'" in result["error"]["message"]


def test_every_region_has_a_delay_step_to_itself():
    """A delay of 0 is a step, so a path whose time stops at the invariant bound
    x=2 still goes on."""
    fixture = str(_FIXTURE.with_name("tctl_tol_minimal.txt"))
    result = model_checking("{J0}G true", fixture)
    assert _states_from_result(result) == {"s0"}
    assert result["initial_state"] == "Initial state s0: True"


def test_demon_cannot_disable_the_only_edge():
    """The edge s0 -> s1 must stay enabled, so leaving s0 at x=1 never meets p."""
    fixture = str(_FIXTURE.with_name("tol_only_edge.txt"))
    result = model_checking("{J1}F (p : x>3)", fixture)
    assert result["initial_state"] == "Initial state s0: False"


def test_syntax_error():
    result = model_checking("{J2}F p (", str(_FIXTURE))
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
