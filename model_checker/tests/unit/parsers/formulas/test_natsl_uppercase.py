"""NatSL parser accepts uppercase binding variables and propositions."""

import pytest

from model_checker.parsers.formulas.NatSL.parser import NatSLParser


@pytest.mark.unit
def test_natsl_parser_accepts_uppercase_proposition():
    parser = NatSLParser()
    formula = "E{1}Goal:(Goal,1)F Goal"
    assert parser.parse(formula) is not None
