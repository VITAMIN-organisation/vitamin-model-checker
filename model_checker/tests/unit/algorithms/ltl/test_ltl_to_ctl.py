"""LTL to CTL conversion: formula mapping, correctness."""

import pytest

from model_checker.parsers.formulas.LTL.ltl_to_ctl import ltl_to_ctl


@pytest.mark.parametrize(
    "ltl_formula,expected_ctl",
    [
        ("Xp", "AXp"),
        ("FGp", "AFAGp"),
        ("AXp", "AXp"),
    ],
)
def test_ltl_to_ctl_basic_complex_and_idempotent(ltl_formula, expected_ctl):
    """Covers basic conversion, nested operators, and idempotent CTL formulas."""
    assert ltl_to_ctl(ltl_formula) == expected_ctl
