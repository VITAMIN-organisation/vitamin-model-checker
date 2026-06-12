"""Unit tests for IATL formula parser syntax alignment."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.fixture
def parser():
    return FormulaParserFactory.get_parser_instance("IATL")


@pytest.mark.parametrize(
    "formula",
    [
        "<1>X p",
        "<1,2>F q",
        "[1]G p",
        "[1,2]X r",
        "<1>(p U q)",
        "[1](p R q)",
        "p -> q",
        "!p",
    ],
)
def test_valid_iatl_formulas(parser, formula):
    assert parser.parse(formula, n_agent=2) is not None


@pytest.mark.parametrize(
    "formula",
    [
        "<<1>>X p",
        "<>X p",
        "[]G p",
        "<1><2>F p",
    ],
)
def test_rejects_non_project_coalition_syntax(parser, formula):
    assert parser.parse(formula, n_agent=2) is None
