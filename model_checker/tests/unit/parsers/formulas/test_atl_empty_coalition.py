"""ATL parser: empty coalition <> support."""

import pytest

from model_checker.parsers.formulas.ATL.parser import ATLParser


@pytest.mark.unit
def test_atl_parser_accepts_empty_coalition_eventually():
    parser = ATLParser()
    result = parser.parse("<> F p", n_agent=1)
    assert result is not None


@pytest.mark.unit
def test_atl_parser_accepts_empty_coalition_globally():
    parser = ATLParser()
    result = parser.parse("<> G p", n_agent=2)
    assert result is not None


@pytest.mark.unit
def test_atl_parser_still_rejects_trailing_comma_coalition():
    parser = ATLParser()
    result = parser.parse("<1,> F p", n_agent=1)
    assert result is None
