"""NatSL !F conversion and existential-universal semantics."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.NatSL.conversion import (
    convert_parsed_natsl_to_natatl_separated,
)


@pytest.mark.unit
def test_natsl_parser_accepts_not_eventually():
    parser = FormulaParserFactory.get_parser_instance("NatSL")
    parsed = parser.parse("E{1}x:(x,1)!F goal")
    assert parsed is not None
    existential, universal = convert_parsed_natsl_to_natatl_separated(
        parsed, original_formula="E{1}x:(x,1)!F goal"
    )
    assert existential
    assert existential[0].startswith("!")
