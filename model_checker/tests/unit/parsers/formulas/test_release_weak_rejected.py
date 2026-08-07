"""Release and Weak Until rejection for logics without R/W solvers."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic,formula",
    [
        ("OATL", "<1><5>R p"),
        ("OATL", "<1><5>W p"),
        ("OATL", "<1><5> p R q"),
        ("OATL", "<1><5> p W q"),
        ("RBATL", "<1><5>R p"),
        ("RBATL", "<1,2><3>W q"),
        ("RBATL", "<1><5> p R q"),
        ("RBATL", "<1><5> p W q"),
    ],
)
def test_release_weak_rejected(logic, formula):
    parser = FormulaParserFactory.get_parser_instance(logic)
    result = parser.parse(formula, n_agent=3)
    assert result is None
    assert parser.errors
    assert "Release" in parser.errors[0] or "Weak" in parser.errors[0]


@pytest.mark.unit
def test_capatl_accepts_binary_release():
    """CapATL path formulas include Release; binary R must parse."""
    parser = FormulaParserFactory.get_parser_instance("CapATL")
    result = parser.parse("<{1}, 1> p R q", n_agent=3)
    assert result == ("<{1}, 1>R", "p", "q")
    assert not parser.errors


@pytest.mark.unit
def test_cotl_accepts_binary_release_and_weak():
    """COTL implements R/W; binary forms must remain accepted."""
    parser = FormulaParserFactory.get_parser_instance("COTL")
    assert parser.parse("<1><5> p R q") == ("<1><5>R", "p", "q")
    assert parser.parse("<1><5> p W q") == ("<1><5>W", "p", "q")


@pytest.mark.unit
def test_rbatl_proposition_r_not_treated_as_release():
    """Lowercase proposition r must not trigger Release rejection."""
    parser = FormulaParserFactory.get_parser_instance("RBATL")
    result = parser.parse("<1><2>F r", n_agent=3)
    assert result is not None
    assert not parser.errors
