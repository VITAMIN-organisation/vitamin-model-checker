"""NatSL parser accepts negated eventually goals."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
def test_natsl_parser_accepts_not_eventually():
    parser = FormulaParserFactory.get_parser_instance("NatSL")
    parsed = parser.parse("E{1}x:(x,1)!F goal")
    assert parsed is not None
    assert parsed.goal.operator == "F"
    assert parsed.goal.negated is True
    assert parsed.goal.proposition == "goal"
