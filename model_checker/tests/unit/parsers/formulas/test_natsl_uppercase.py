"""NatSL parser: shared atomic proposition policy for bindings and temporal atoms."""

import pytest

from model_checker.parsers.formulas.NatSL.parser import NatSLParser


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "E{1}Goal:(Goal,1)F Goal",
        "E{1}x:(x,1)F p",
        "E{2}myVar:(myVar,1)F safe_1",
        "E{1}x:(x,1)F win",
        "A{1}y:(y,1)!F fail",
    ],
)
def test_natsl_parser_accepts_standard_atomic_propositions(formula):
    assert NatSLParser().parse(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula,error_fragment",
    [
        ("E{1}x:(x,1)F exist", "reserved keyword"),
        ("E{1}x:(x,1)F forall", "reserved keyword"),
        ("E{1}x:(x,1)F and", "reserved keyword"),
    ],
)
def test_natsl_parser_rejects_reserved_temporal_atoms(formula, error_fragment):
    parser = NatSLParser()
    assert parser.parse(formula) is None
    assert any(error_fragment in err.lower() for err in parser.errors)


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "E{1}x:(x,1)F 1goal",
        "E{1}x:(x,1)F eventually",
        "E{1}x:(x,1)F not",
    ],
)
def test_natsl_parser_rejects_unparseable_temporal_atoms(formula):
    assert NatSLParser().parse(formula) is None


@pytest.mark.unit
def test_natsl_parser_rejects_uppercase_quantifier_as_temporal_atom():
    """E and A are NatSL quantifier tokens and cannot name temporal atoms."""
    for formula in ("E{1}x:(x,1)F E", "A{1}y:(y,1)F A"):
        assert NatSLParser().parse(formula) is None
