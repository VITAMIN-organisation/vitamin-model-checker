"""NatSL parser: mixed-case bindings; temporal atoms restricted to a-h."""

import pytest

from model_checker.parsers.formulas.NatSL.parser import NatSLParser


@pytest.mark.unit
def test_natsl_parser_accepts_uppercase_binding_with_temporal_a_h():
    parser = NatSLParser()
    formula = "E{1}Goal:(Goal,1)F a"
    assert parser.parse(formula) is not None


@pytest.mark.unit
def test_natsl_parser_rejects_uppercase_temporal_atom():
    parser = NatSLParser()
    formula = "E{1}Goal:(Goal,1)F Goal"
    assert parser.parse(formula) is None
    assert any("a-h" in err for err in parser.errors)
