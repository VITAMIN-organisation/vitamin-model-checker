"""NatSL parser accepts flexible whitespace around tokens, but not inside a goal."""

import pytest

from model_checker.parsers.formulas.NatSL.parser import (
    NatSLParseError,
    format_formula,
    parse_formula,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula,expected",
    [
        ("E{1}xA{1}y:(x,1)(y,2)F goal", "E{1}xA{1}y:(x,1)(y,2)F goal"),
        (
            "E {1} x A {1} y : ( x , 1 ) ( y , 2 ) F  goal",
            "E{1}xA{1}y:(x,1)(y,2)F goal",
        ),
        ("E{1}x:(x,1) not F goal", "E{1}x:(x,1)!F goal"),
        ("E{1}x:(x,1) F Goal", "E{1}x:(x,1)F Goal"),
    ],
)
def test_natsl_spacing_variants_normalize(formula, expected):
    assert format_formula(parse_formula(formula)) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "E{1}x:(x,1)Fgoal",
        "E{1}x:(x,1) Fgoal",
        "E{1}x:(x,1)!Fgoal",
        "E{1}x:(x,1) Goal",
    ],
)
def test_natsl_goal_operator_needs_a_space(formula):
    """`Fgoal` and `Goal` are names, not an operator and a name."""
    with pytest.raises(NatSLParseError, match="space after it"):
        parse_formula(formula)


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "E{1}x:(x,1)f goal",
        "E{1}x:(x,1)g goal",
        "E{1}x:(x,1)x goal",
        "E{1}x:(x,1)!f goal",
        "E{1}x:(x,1) not f goal",
        "E{1}x:(x,1) NOT F goal",
    ],
)
def test_natsl_goal_operator_is_uppercase(formula):
    """`f goal` is not an operator: operators are uppercase, `not` lowercase."""
    with pytest.raises(NatSLParseError, match="uppercase operator"):
        parse_formula(formula)
