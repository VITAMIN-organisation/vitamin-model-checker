"""RBATL and RABATL have no Release or Weak Until solver, so R and W are rejected by name."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


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
@pytest.mark.parametrize("name", ["r", "w"])
def test_lowercase_r_and_w_are_names(logic, name):
    """The R/W check matches the uppercase operators only."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(f"<1><2>F {name}", n_agent=3) == ("<1><2>F", name)
