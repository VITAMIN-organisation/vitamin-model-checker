"""OL parser: canonical <Jk> demonic cost prefixes only."""

import pytest

from model_checker.parsers.formulas.OL.parser import OLParser


@pytest.mark.unit
def test_ol_parser_accepts_canonical_cost_prefix():
    parser = OLParser()
    spaced = parser.parse("<J2> F safe", n_agent=1)
    glued = parser.parse("<J2>F safe", n_agent=1)
    assert spaced is not None
    assert glued == spaced


@pytest.mark.unit
@pytest.mark.parametrize(
    ("flat", "grouped", "tree"),
    [
        ("<J2> p R q", "<J2> (p R q)", ("<J2>R", "p", "q")),
        ("<J2> p W q", "<J2> (p W q)", ("<J2>W", "p", "q")),
    ],
)
def test_ol_parser_release_and_weak_until_take_optional_parentheses(
    flat, grouped, tree
):
    # Until is covered for every prefix logic in test_until_after_prefix.py.
    parser = OLParser()
    assert parser.parse(flat, n_agent=1) == tree
    assert parser.parse(grouped, n_agent=1) == tree


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["<2> F safe", "F safe", "<J0> F safe"])
def test_ol_parser_rejects_non_canonical_cost_prefix(formula):
    parser = OLParser()
    assert parser.parse(formula, n_agent=1) is None
