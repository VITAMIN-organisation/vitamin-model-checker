"""ATL parser: reject empty coalition <>."""

import pytest

from model_checker.parsers.formulas.ATL.parser import ATLParser


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["<> F p", "<> G p", "<>F p"])
def test_atl_parser_rejects_empty_coalition(formula):
    assert ATLParser().parse(formula, n_agent=2) is None


@pytest.mark.unit
def test_atl_parser_still_rejects_trailing_comma_coalition():
    assert ATLParser().parse("<1,> F p", n_agent=1) is None
