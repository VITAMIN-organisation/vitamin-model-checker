"""LTL to CTL conversion: formula mapping, correctness."""

import pytest

from model_checker.parsers.formulas.CTL.parser import CTLParser
from model_checker.parsers.formulas.LTL.ltl_to_ctl import ltl_to_ctl

_CASES = [
    ("X p", "AX p"),
    ("F G p", "AF AG p"),
    ("G F p", "AG AF p"),
    ("G (p -> F q)", "AG (p -> (AF q))"),
    ("p U q", "A(p U q)"),
    ("p until q", "A(p U q)"),
    ("(p)U(q)", "A(p U q)"),
    ("p U(q)", "A(p U q)"),
    ("p U !q", "A(p U (!q))"),
    ("(p && q) U (r || s)", "A((p && q) U (r || s))"),
    ("F (p U q)", "AF A(p U q)"),
    ("not p or q", "(!p) || q"),
    ("F p && q", "(AF p) && q"),
    ("(F p) U q", "A((AF p) U q)"),
    # The parser reads U as right-associative, and `!p U q` as `!(p U q)`.
    ("p U q U r", "A(p U A(q U r))"),
    ("(p U q) U r", "A(A(p U q) U r)"),
    ("!p U q", "!A(p U q)"),
]


@pytest.mark.parametrize("ltl_formula,expected_ctl", _CASES)
def test_ltl_to_ctl_maps_the_parsed_formula(ltl_formula, expected_ctl):
    assert ltl_to_ctl(ltl_formula) == expected_ctl


@pytest.mark.parametrize("ltl_formula", [f for f, _ in _CASES])
def test_ltl_to_ctl_output_parses_as_ctl(ltl_formula):
    assert CTLParser().parse(ltl_to_ctl(ltl_formula)) is not None


@pytest.mark.parametrize(
    "glued_formula",
    ["Xp", "Fp", "FGp", "GFp", "AXp", "AGAFp", "FFuel", "Fgoal", "pUq"],
)
def test_ltl_to_ctl_leaves_an_operator_glued_to_a_name_alone(glued_formula):
    """`Fp` is one name, so it is not split into `F p`; operators need a space."""
    assert ltl_to_ctl(glued_formula) == glued_formula


@pytest.mark.parametrize("formula", ["pU q", "p Uq", "p U", "F", "AX p"])
def test_ltl_to_ctl_rejects_a_formula_the_parser_rejects(formula):
    with pytest.raises(ValueError, match=f"Invalid LTL formula '{formula}'"):
        ltl_to_ctl(formula)
