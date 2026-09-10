from __future__ import annotations

import pytest

from model_checker.parsers.formulas.ATL_STAR.formula import (
    And,
    Coalition,
    Next,
    Not,
    Prop,
    True_,
    Until,
)
from model_checker.parsers.formulas.ATL_STAR.grammar import ATLStarParseError, parse


def test_atom():
    assert parse("p") == Prop("p")


def test_true_false():
    assert parse("true") == True_()
    assert parse("false") == Not(True_())


def test_negation():
    assert parse("!p") == Not(Prop("p"))
    assert parse("not p") == Not(Prop("p"))


def test_conjunction_left_associative():
    assert parse("p & q & r") == And(And(Prop("p"), Prop("q")), Prop("r"))


def test_and_binds_tighter_than_or():
    assert parse("p & q | r") == Not(And(Not(And(Prop("p"), Prop("q"))), Not(Prop("r"))))


def test_lowercase_single_letter_stays_a_prop():
    # Only uppercase X/F/G/U are reserved, lowercase single-letter names
    # (common for propositions) stay available as identifiers.
    assert parse("x & g") == And(Prop("x"), Prop("g"))


def test_next():
    assert parse("X p") == Next(Prop("p"))
    assert parse("next p") == Next(Prop("p"))


def test_until():
    assert parse("p U q") == Until(Prop("p"), Prop("q"))
    assert parse("p until q") == Until(Prop("p"), Prop("q"))


def test_eventually_desugars_to_until_true():
    assert parse("F p") == Until(True_(), Prop("p"))


def test_globally_desugars_to_not_until_true_not():
    assert parse("G p") == Not(Until(True_(), Not(Prop("p"))))


def test_implies_desugars():
    assert parse("p -> q") == Not(And(Prop("p"), Not(Prop("q"))))


def test_coalition_bare_atom():
    assert parse("<<1,2>>p") == Coalition(frozenset({1, 2}), Prop("p"))


def test_coalition_over_negation_and_next():
    assert parse("<<1>>!p") == Coalition(frozenset({1}), Not(Prop("p")))
    assert parse("<<1>>X p") == Coalition(frozenset({1}), Next(Prop("p")))


def test_coalition_requires_parens_for_until():
    assert parse("<<1>>(p U q)") == Coalition(frozenset({1}), Until(Prop("p"), Prop("q")))


def test_bare_until_after_coalition_only_wraps_first_operand():
    # <<1>>p U q means (<<1>>p) U q, not <<1>>(p U q), ATL*'s nesting (unlike
    # ATL) needs explicit parens for the coalition to scope over a compound
    # path formula.
    assert parse("<<1>>p U q") == Until(Coalition(frozenset({1}), Prop("p")), Prop("q"))


def test_nested_coalition():
    assert parse("<<1>>X<<2>>p") == Coalition(
        frozenset({1}), Next(Coalition(frozenset({2}), Prop("p")))
    )


def test_parentheses_group():
    assert parse("(p & q) U r") == Until(And(Prop("p"), Prop("q")), Prop("r"))


def test_num_agents_accepts_in_range():
    parse("<<1,2>>p", num_agents=2)


def test_num_agents_rejects_out_of_range():
    with pytest.raises(ATLStarParseError):
        parse("<<1,3>>p", num_agents=2)


def test_num_agents_error_points_at_the_actual_offending_token():
    # The out-of-range agent id is "3", the 4th character (0-based), not
    # position 0, which a previous, separate post-parse validation pass
    # always reported regardless of where the real problem was.
    with pytest.raises(ATLStarParseError) as excinfo:
        parse("<<1,3>>p", num_agents=2)
    assert excinfo.value.position == 4


def test_duplicate_agent_error_points_at_the_duplicate_token_not_the_first():
    with pytest.raises(ATLStarParseError) as excinfo:
        parse("<<1,2,1>>p")
    assert excinfo.value.position == 6


def test_num_agents_checks_nested_coalitions():
    with pytest.raises(ATLStarParseError):
        parse("<<1>>X<<5>>p", num_agents=2)


def test_num_agents_checks_inside_and():
    with pytest.raises(ATLStarParseError):
        parse("<<1>>(p & <<5>>q)", num_agents=2)


def test_num_agents_checks_inside_until():
    with pytest.raises(ATLStarParseError):
        parse("<<1>>(p U <<5>>q)", num_agents=2)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "p &",
        "(p & q",
        "<<1,1>>p",
        "<<>>p",
        "<<1>>",
        "p q",
        "p U",
        "@",
    ],
)
def test_malformed_input_raises(text):
    with pytest.raises(ATLStarParseError):
        parse(text)
