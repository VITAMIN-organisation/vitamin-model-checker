"""ATL* grammar: the tree each form builds, and where an error points.

The parser turns F, G, ->, || and false into U, !, && and true, so those trees are
checked exactly. `<<1>> p U q` is `<<1>> (p U q)` (JACM 2002, p. 689); a connective
next to a bare U or after a coalition is ambiguous and must be parenthesized.
"""

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

pytestmark = pytest.mark.atl_star

_P, _Q, _R = Prop("p"), Prop("q"), Prop("r")


@pytest.mark.parametrize(
    ("text", "tree"),
    [
        ("true", True_()),
        ("false", Not(True_())),
        ("F p", Until(True_(), _P)),
        ("G p", Not(Until(True_(), Not(_P)))),
        ("p -> q", Not(And(_P, Not(_Q)))),
        ("p && q || r", Not(And(Not(And(_P, _Q)), Not(_R)))),
        ("p && q && r", And(And(_P, _Q), _R)),
    ],
)
def test_sugar_desugars_to_the_core_operators(text, tree):
    """The solver sees only Prop, True, Not, And, Next, Until and Coalition."""
    assert parse(text) == tree


@pytest.mark.parametrize(
    ("word", "symbol"), [("not p", "!p"), ("next p", "X p"), ("p until q", "p U q")]
)
def test_word_forms_build_the_symbol_tree(word, symbol):
    """`not`, `next` and `until` are the operators, not names."""
    assert parse(word) == parse(symbol)


def test_lowercase_single_letter_is_a_name():
    """Only uppercase X, F, G and U are operators, so `x && g` is two names."""
    assert parse("x && g") == And(Prop("x"), Prop("g"))


@pytest.mark.parametrize(
    ("text", "tree"),
    [
        ("<<1,2>>p", Coalition(frozenset({1, 2}), _P)),
        ("<<1>>!p", Coalition(frozenset({1}), Not(_P))),
        ("<<1>>(p U q)", Coalition(frozenset({1}), Until(_P, _Q))),
        ("(<<1>>p) U q", Until(Coalition(frozenset({1}), _P), _Q)),
        (
            "<<2>>((<<1>>p) U q)",
            Coalition(frozenset({2}), Until(Coalition(frozenset({1}), _P), _Q)),
        ),
        ("<<1>>X p U q", Coalition(frozenset({1}), Until(Next(_P), _Q))),
        (
            "<<1>>X<<2>>p",
            Coalition(frozenset({1}), Next(Coalition(frozenset({2}), _P))),
        ),
        ("(p && q) U r", Until(And(_P, _Q), _R)),
    ],
)
def test_coalition_scope(text, tree):
    """A coalition covers what follows it up to the closing parenthesis."""
    assert parse(text) == tree


def test_until_after_a_nested_coalition_belongs_to_the_inner_one():
    """`<<2>><<1>>p U q` reads U under <<1>>, with or without parentheses."""
    expected = Coalition(frozenset({2}), Coalition(frozenset({1}), Until(_P, _Q)))
    assert parse("<<2>>(<<1>>p U q)") == expected
    assert parse("<<2>><<1>>p U q") == expected


@pytest.mark.parametrize(
    ("text", "shown", "position"),
    [
        ("p U q && r", "'x U y && z'", 2),
        ("p && q U r", "'x && y U z'", 7),
        ("p -> q U r", "'x -> y U z'", 7),
        ("<<1>> (p U q || r)", "'x U y || z'", 9),
    ],
)
def test_until_next_to_a_connective_is_ambiguous(text, shown, position):
    """The error shows the shape and points at the U."""
    with pytest.raises(ATLStarParseError, match="is ambiguous") as excinfo:
        parse(text)
    assert shown in str(excinfo.value)
    assert excinfo.value.position == position


@pytest.mark.parametrize(
    ("text", "position"),
    [
        ("<<1>> p && q", 0),
        ("<<1>> F p && q", 0),
        ("<<1>> (p U q) && r", 0),
        ("r || !<<2>> X p -> q", 6),
    ],
)
def test_connective_after_a_coalition_is_ambiguous(text, position):
    """The error points at the coalition whose scope is unclear."""
    with pytest.raises(ATLStarParseError, match="is ambiguous") as excinfo:
        parse(text)
    assert excinfo.value.position == position


@pytest.mark.parametrize(
    ("text", "position"), [("p U q U r", 6), ("<<1>> p U q U r", 12)]
)
def test_until_does_not_chain(text, position):
    """`p U q U r` has no agreed grouping; the error points at the second U."""
    with pytest.raises(ATLStarParseError, match="U does not chain") as excinfo:
        parse(text)
    assert excinfo.value.position == position


@pytest.mark.parametrize(
    ("text", "num_agents", "position"),
    [("<<1,3>>p", 2, 4), ("<<1,2,1>>p", None, 6)],
)
def test_agent_error_points_at_the_offending_token(text, num_agents, position):
    """An out-of-range or repeated agent is reported where it is written."""
    with pytest.raises(ATLStarParseError) as excinfo:
        parse(text, num_agents=num_agents)
    assert excinfo.value.position == position


@pytest.mark.parametrize("text", ["", "p &&", "(p && q", "<<1>>", "p q", "p U", "@"])
def test_malformed_input_raises(text):
    """Empty input, a missing operand or parenthesis, or a stray token."""
    with pytest.raises(ATLStarParseError):
        parse(text)
