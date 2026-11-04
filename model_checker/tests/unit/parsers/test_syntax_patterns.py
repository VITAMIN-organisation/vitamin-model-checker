"""Shared syntax tokens: matching behavior, not just constant membership."""

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
    NATATL_CAPACITY_RE,
    OATL_COALITION_BUDGET_TOKEN,
    PROPOSITION_FULL_RE,
    WALLET_CONSTRAINT_RE,
)


@pytest.mark.unit
def test_proposition_pattern_rejects_leading_digit_and_reserved_shape():
    assert PROPOSITION_FULL_RE.match("Goal")
    assert PROPOSITION_FULL_RE.match("safe_1")
    assert not PROPOSITION_FULL_RE.match("1goal")
    assert not PROPOSITION_FULL_RE.match("p-q")


@pytest.mark.unit
def test_natatl_capacity_captures_agents_and_bound():
    match = NATATL_CAPACITY_RE.match("<{1,2}, 5>")
    assert match is not None
    assert match.group(1) == "1,2"
    assert match.group(2) == "5"
    assert NATATL_CAPACITY_RE.match("<{1,2}>") is None
    assert NATATL_CAPACITY_RE.match("<1,2>, 5>") is None


@pytest.mark.unit
def test_clock_bound_regex_keeps_two_char_operators_intact():
    """>= must not be lexed as > plus a leftover '=' (the old DBM split)."""
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
    assert CELL_CONSTRAINT_RE.fullmatch("x>=3")
    assert CELL_CONSTRAINT_RE.fullmatch("x=0")
    assert not CELL_CONSTRAINT_RE.fullmatch("x>3y")
    assert INVARIANT_RE.fullmatch("x<=5")
    assert INVARIANT_RE.fullmatch("x<5")
    assert not INVARIANT_RE.fullmatch("x>=5")
    assert not INVARIANT_RE.fullmatch("x=0")


@pytest.mark.unit
def test_wallet_constraint_pattern_rejects_unknown_operator():
    ok = WALLET_CONSTRAINT_RE.fullmatch("wallet(1, >= 5)")
    assert ok is not None
    assert ok.group("agent", "operator", "value") == ("1", ">=", "5")
    assert WALLET_CONSTRAINT_RE.fullmatch("wallet(1, => 5)") is None
    assert WALLET_CONSTRAINT_RE.fullmatch("wallet(1, = 5)") is None


@pytest.mark.unit
def test_cotl_legion_token_accepts_empty_legion_and_zero_budget():
    assert re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1,2><3>")
    assert re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<><0>")
    assert not re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1><05>")
    assert not re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1,><2>")
    assert not re.fullmatch(COTL_LEGION_BUDGET_TOKEN, "<1>F")


@pytest.mark.unit
def test_oatl_budget_token_accepts_zero_but_not_leading_zeros():
    assert re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1><0>")
    assert re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1,2><10>")
    assert not re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1><05>")
    assert not re.fullmatch(OATL_COALITION_BUDGET_TOKEN, "<1>F")
