"""RBATL and RABATL have no Release or Weak Until solver, so R and W are rejected by name."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.tests.helpers.formula_cases import parse_errors


@pytest.mark.unit
@pytest.mark.parametrize("logic", ["RBATL", "RABATL"])
@pytest.mark.parametrize(
    "formula", ["<1><5>R p", "<1,2><3>W q", "<1><5> p R q", "<1><5> p W q"]
)
def test_release_and_weak_until_are_rejected_with_a_message(logic, formula):
    """The user is told the operator is unsupported, not given a bare syntax error."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(formula, n_agent=3) is None
    assert "does not support Release (R) or Weak Until (W)" in parser.errors[0]


@pytest.mark.unit
@pytest.mark.parametrize("logic", ["RBATL", "RABATL"])
@pytest.mark.parametrize("formula", ["<1><5> p Weak q", "<1><5> p RELEASE q"])
def test_word_in_another_letter_case_is_not_read_as_the_operator(logic, formula):
    """Word operators are lowercase only, so `Weak` is a syntax error, not W."""
    errors = parse_errors(logic, formula, n_agent=3)
    assert "Syntax error near token" in errors[0], errors


@pytest.mark.unit
@pytest.mark.parametrize("logic", ["RBATL", "RABATL"])
@pytest.mark.parametrize(
    "name", ["r", "w", "isweak", "p_weak", "myrelease", "p_release"]
)
def test_names_are_not_mistaken_for_r_or_w(logic, name):
    """The check matches uppercase R and W and the whole words release and weak."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(f"<1><2>F {name}", n_agent=3) == ("<1><2>F", name)
