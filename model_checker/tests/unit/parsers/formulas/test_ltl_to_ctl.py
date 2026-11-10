"""LTL to CTL rewriting: each temporal operator gets the universal path quantifier A.

The checker answers an LTL formula by checking this CTL text, so the mapping is
pinned case by case and every output must parse as CTL.
"""

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
    # The LTL parser reads U as right-associative, and `!p U q` as `!(p U q)`.
    ("p U q U r", "A(p U A(q U r))"),
    ("(p U q) U r", "A(A(p U q) U r)"),
    ("!p U q", "!A(p U q)"),
]


@pytest.mark.unit
@pytest.mark.parametrize(("ltl_formula", "expected_ctl"), _CASES)
def test_each_operator_gets_the_path_quantifier(ltl_formula, expected_ctl):
    """The CTL text follows the LTL parse tree, parentheses included."""
    assert ltl_to_ctl(ltl_formula) == expected_ctl


@pytest.mark.unit
@pytest.mark.parametrize("ltl_formula", [f for f, _ in _CASES])
def test_output_parses_as_ctl(ltl_formula):
    """A rewrite the CTL parser rejects would turn every LTL query into an error."""
    assert CTLParser().parse(ltl_to_ctl(ltl_formula)) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "glued_formula",
    ["Xp", "Fp", "FGp", "GFp", "AXp", "AGAFp", "FFuel", "Fgoal", "pUq"],
)
def test_operator_glued_to_a_name_stays_one_name(glued_formula):
    """`Fp` is a name, so it passes through unchanged."""
    assert ltl_to_ctl(glued_formula) == glued_formula


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["pU q", "p Uq", "p U", "F", "AX p"])
def test_formula_the_parser_rejects_is_an_error(formula):
    """The error names the formula instead of returning broken CTL."""
    with pytest.raises(ValueError, match=f"Invalid LTL formula '{formula}'"):
        ltl_to_ctl(formula)
