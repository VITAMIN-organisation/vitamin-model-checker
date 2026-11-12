"""NatSL formulas: quantifier prefix, bindings and one temporal goal.

`E{k}x A{k}y: (x, 1)(y, 2) F goal` quantifies strategy variables with a complexity
bound, binds each to one agent, and ends in a goal `F`, `G` or `X` on one name,
optionally negated. The goal takes no connective.
"""

import pytest

from model_checker.parsers.formulas.NatSL.parser import (
    NatSLParseError,
    NatSLParser,
    format_formula,
    goal_to_ctl,
    parse_formula,
)


@pytest.mark.unit
def test_prefix_bindings_and_goal_are_read_in_order():
    """Multi-letter variables keep their order, bounds and agents."""
    parsed = parse_formula(
        "E{2}controller A{1}opponent: (controller, 1)(opponent, 2) G goal"
    )
    assert [(q.kind, q.variable, q.bound) for q in parsed.quantifiers] == [
        ("E", "controller", 2),
        ("A", "opponent", 1),
    ]
    assert parsed.bindings == (("controller", 1), ("opponent", 2))
    assert (parsed.goal.operator, parsed.goal.proposition) == ("G", "goal")
    assert parsed.goal.negated is False


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "normal_form"),
    [
        ("E{1}xA{1}y:(x,1)(y,2)F goal", "E{1}xA{1}y:(x,1)(y,2)F goal"),
        (
            "E {1} x A {1} y : ( x , 1 ) ( y , 2 ) F  goal",
            "E{1}xA{1}y:(x,1)(y,2)F goal",
        ),
        ("E{1}x:(x,1) not F goal", "E{1}x:(x,1)!F goal"),
        ("E{1}x:(x,1) F gOAL", "E{1}x:(x,1)F gOAL"),
    ],
)
def test_spacing_outside_the_goal_is_free(formula, normal_form):
    """Spaces between tokens do not matter; `not` and `!` are one negation."""
    assert format_formula(parse_formula(formula)) == normal_form


@pytest.mark.unit
@pytest.mark.parametrize(
    ("goal", "ctl"),
    [
        ("F goal", "AF goal"),
        ("!F goal", "AG !goal"),
        ("G goal", "AG goal"),
        ("!G goal", "AF !goal"),
        ("X goal", "AX goal"),
        ("!X goal", "AX !goal"),
    ],
)
def test_goal_becomes_a_universal_ctl_formula(goal, ctl):
    """Once all strategies are fixed every path counts, so `!F goal` is `AG !goal`."""
    assert goal_to_ctl(parse_formula(f"E{{1}}x: (x, 1) {goal}").goal) == ctl


@pytest.mark.unit
def test_negating_the_whole_formula_flips_every_quantifier_and_the_goal():
    """`!(E x: ... F p)` is `A x: ... !F p`, the dual."""
    parsed = parse_formula("!(E{1}x A{2}y:(x,1)(y,2)F p)")
    assert format_formula(parsed) == "A{1}xE{2}y:(x,1)(y,2)!F p"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "message"),
    [
        ("E{0}x:(x,1)F p", "bounds must be positive"),
        ("E{1}x E{1}x:(x,1)(x,2)F p", "quantified exactly once"),
        ("E{1}x:(y,1)F p", "exactly one binding"),
        ("E{1}x A{2}y:(x,1)F p", "exactly one binding"),
        ("E{1}x E{1}y:(x,1)(y,1)F p", "only one binding"),
        ("E{1}x(x,1)F p", "Missing ':'"),
    ],
)
def test_inconsistent_prefix_or_bindings_are_rejected(formula, message):
    """Bound 0, a variable quantified twice or unbound, an agent bound twice, a missing ':'."""
    with pytest.raises(NatSLParseError, match=message):
        parse_formula(formula)


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
def test_goal_operator_needs_a_space(formula):
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
        "E{1}x:(x,1) NOT F goal",
    ],
)
def test_goal_operator_is_uppercase_and_not_is_lowercase(formula):
    """`f goal` and `NOT F goal` are rejected."""
    with pytest.raises(NatSLParseError, match="uppercase operator"):
        parse_formula(formula)


@pytest.mark.unit
@pytest.mark.parametrize("connective", ["&&", "||", "->", "and", "or", "implies"])
def test_goal_takes_no_connective(connective):
    """Neither reading of `F p && q` is a NatSL goal."""
    with pytest.raises(NatSLParseError, match="Unsupported goal"):
        parse_formula(f"E{{1}}x:(x,1) F p {connective} q")


@pytest.mark.unit
@pytest.mark.parametrize("name", ["E", "A"])
def test_quantifier_letter_is_not_a_goal_name(name):
    """E and A start a quantifier and a name starts lowercase, so the factory's
    NatSL parser refuses them as the goal."""
    parser = NatSLParser()
    assert parser.parse(f"E{{1}}x:(x,1)F {name}") is None
    assert any(f"'{name}' is invalid" in error for error in parser.errors)
