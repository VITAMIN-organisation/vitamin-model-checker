"""Release and Weak Until rejection for logics without R/W solvers."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic,formula",
    [
        ("OATL", "<1><5>R p"),
        ("OATL", "<1><5>W p"),
        ("RBATL", "<1><5>R p"),
        ("RBATL", "<1,2><3>W q"),
        ("CapATL", "<{1}, 1>R p"),
    ],
)
def test_release_weak_rejected(logic, formula):
    parser = FormulaParserFactory.get_parser_instance(logic)
    result = parser.parse(formula, n_agent=3)
    assert result is None
    assert parser.errors
    assert "Release" in parser.errors[0] or "Weak" in parser.errors[0]
