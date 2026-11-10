"""Shared regular expressions for clock constraints, wallet guards and cost budgets."""

import re

import pytest

from model_checker.parsers.game_structures.timed_cgs.constraint_syntax import (
    BOUND_RE,
    CELL_CONSTRAINT_RE,
    INVARIANT_RE,
    RESET_RE,
)
from model_checker.parsers.syntax_patterns import (
    COTL_LEGION_BUDGET_TOKEN,
    OATL_COALITION_BUDGET_TOKEN,
)


@pytest.mark.unit
def test_clock_bound_regex_keeps_two_char_operators_intact():
    """`x>=3` is clock x, `>=`, 3, never `>` then a stray `=`; `x=0` is a reset."""
    ge = BOUND_RE.fullmatch("x>=3")
    gt = BOUND_RE.fullmatch("x>3")
    assert ge is not None and ge.groups() == ("x", ">=", "3")
    assert gt is not None and gt.groups() == ("x", ">", "3")
    eq = BOUND_RE.fullmatch("x==3")
    assert eq is not None and eq.groups() == ("x", "==", "3")
    assert BOUND_RE.fullmatch("x=0") is None
    reset = RESET_RE.fullmatch("x=0")
    assert reset is not None and reset.groups() == ("x", "0")


@pytest.mark.unit
def test_file_cell_accepts_bound_or_reset_invariants_are_upper_bounds():
    """A transition cell holds a bound or a reset; an invariant only `<` or `<=`."""
    assert CELL_CONSTRAINT_RE.fullmatch("x>=3")
    assert CELL_CONSTRAINT_RE.fullmatch("x=0")
    assert not CELL_CONSTRAINT_RE.fullmatch("x>3y")
    assert INVARIANT_RE.fullmatch("x<=5")
    assert INVARIANT_RE.fullmatch("x<5")
    assert not INVARIANT_RE.fullmatch("x>=5")
    assert not INVARIANT_RE.fullmatch("x=0")


@pytest.mark.unit
def test_cotl_legion_token_accepts_empty_legion_and_zero_budget():
    """`<><0>` is valid COTL; a leading zero or trailing comma is not."""
    assert re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1,2><3>")
    assert re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<><0>")
    assert not re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1><05>")
    assert not re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1,><2>")
    assert not re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1>F")


@pytest.mark.unit
def test_oatl_budget_token_accepts_zero_but_not_leading_zeros():
    """Budget 0 is allowed; `05` is not a budget."""
    assert re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1><0>")
    assert re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1,2><10>")
    assert not re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1><05>")
    assert not re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1>F")
