"""LTL to CTL conversion: formula mapping, correctness."""

import pytest

from model_checker.parsers.formulas.CTL.parser import CTLParser
from model_checker.parsers.formulas.LTL.ltl_to_ctl import ltl_to_ctl


@pytest.mark.parametrize(
    "ltl_formula,expected_ctl",
    [
        ("X p", "AX p"),
        ("F G p", "AF AG p"),
        ("G F p", "AG AF p"),
        ("G (p -> F q)", "AG (p -> AF q)"),
        ("p U q", "A(p U q)"),
        ("p until q", "A(p U q)"),
        ("AX p", "AX p"),
        ("AG AF p", "AG AF p"),
        ("AF AG p", "AF AG p"),
    ],
)
def test_ltl_to_ctl_basic_complex_and_idempotent(ltl_formula, expected_ctl):
    """Covers basic conversion, nested operators, until, and spaced CTL shape."""
    assert ltl_to_ctl(ltl_formula) == expected_ctl


@pytest.mark.parametrize(
    "glued_formula",
    ["Xp", "Fp", "FGp", "GFp", "AXp", "AGAFp", "FFuel", "Fgoal"],
)
def test_ltl_to_ctl_leaves_an_operator_glued_to_a_name_alone(glued_formula):
    """`Fp` is one name, so it is not split into `F p`; operators need a space."""
    assert ltl_to_ctl(glued_formula) == glued_formula


@pytest.mark.parametrize(
    "ltl_formula",
    [
        "X p",
        "F G p",
        "G F p",
        "p U q",
        "p until q",
        "F G p",
        "AX p",
        "AG AF p",
        "AF AG p",
    ],
)
def test_ltl_to_ctl_output_parses_as_ctl(ltl_formula):
    rewritten = ltl_to_ctl(ltl_formula)
    assert CTLParser().parse(rewritten) is not None
