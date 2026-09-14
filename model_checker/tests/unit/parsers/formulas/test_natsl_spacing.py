"""NatSL parser accepts flexible whitespace around tokens."""

import pytest

from model_checker.parsers.formulas.NatSL.parser import format_formula, parse_formula


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula,expected",
    [
        ("E{1}xA{1}y:(x,1)(y,2)Fgoal", "E{1}xA{1}y:(x,1)(y,2)Fgoal"),
        ("E {1} x A {1} y : ( x , 1 ) ( y , 2 ) F  goal", "E{1}xA{1}y:(x,1)(y,2)Fgoal"),
        ("E{1}x:(x,1) not F goal", "E{1}x:(x,1)!Fgoal"),
    ],
)
def test_natsl_spacing_variants_normalize(formula, expected):
    assert format_formula(parse_formula(formula)) == expected
