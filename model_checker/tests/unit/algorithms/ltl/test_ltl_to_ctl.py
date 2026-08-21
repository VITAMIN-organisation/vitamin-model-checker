"""LTL to CTL conversion: formula mapping, correctness."""

import pytest

from model_checker.parsers.formulas.CTL.parser import CTLParser
from model_checker.parsers.formulas.LTL.ltl_to_ctl import ltl_to_ctl


@pytest.mark.parametrize(
    "ltl_formula,expected_ctl",
    [
        ("Xp", "AX p"),
        ("FGp", "AF AG p"),
        ("GFp", "AG AF p"),
        ("G F p", "AG AF p"),
        ("p U q", "A(p U q)"),
        ("p until q", "A(p U q)"),
        ("AXp", "AX p"),
        ("AGAFp", "AG AF p"),
        ("AFAGp", "AF AG p"),
    ],
)
def test_ltl_to_ctl_basic_complex_and_idempotent(ltl_formula, expected_ctl):
    """Covers basic conversion, nested operators, until, and spaced CTL shape."""
    assert ltl_to_ctl(ltl_formula) == expected_ctl


@pytest.mark.parametrize(
    "ltl_formula",
    [
        "Xp",
        "FGp",
        "GFp",
        "p U q",
        "p until q",
        "G F p",
        "F G p",
        "AXp",
        "AGAFp",
        "AFAGp",
    ],
)
def test_ltl_to_ctl_output_parses_as_ctl(ltl_formula):
    rewritten = ltl_to_ctl(ltl_formula)
    assert CTLParser().parse(rewritten) is not None
