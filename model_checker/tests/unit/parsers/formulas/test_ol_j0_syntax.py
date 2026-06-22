"""OL parser: zero-cost demonic prefix <J0>."""

import pytest

from model_checker.parsers.formulas.OL.parser import OLParser


@pytest.mark.unit
def test_ol_parser_accepts_j0_prefix():
    parser = OLParser()
    result = parser.parse("<J0> F safe", n_agent=1)
    assert result is not None
