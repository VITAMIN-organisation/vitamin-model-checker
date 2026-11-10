"""OL prefixes are `<Jk>`: the Demon with budget k, a natural number."""

import pytest

from model_checker.parsers.formulas.OL.parser import OLParser


@pytest.mark.unit
def test_space_after_the_prefix_is_optional():
    """`<J2> F safe` and `<J2>F safe` build one tree."""
    parser = OLParser()
    spaced = parser.parse("<J2> F safe", n_agent=1)
    assert spaced == ("<J2>F", "safe")
    assert parser.parse("<J2>F safe", n_agent=1) == spaced


@pytest.mark.unit
@pytest.mark.parametrize(
    ("flat", "grouped", "tree"),
    [
        ("<J2> p R q", "<J2> (p R q)", ("<J2>R", "p", "q")),
        ("<J2> p W q", "<J2> (p W q)", ("<J2>W", "p", "q")),
    ],
)
def test_release_and_weak_until_take_optional_parentheses(flat, grouped, tree):
    """Like Until (test_until_after_prefix.py), R and W read the same with parentheses."""
    parser = OLParser()
    assert parser.parse(flat, n_agent=1) == tree
    assert parser.parse(grouped, n_agent=1) == tree


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["<2> F safe", "F safe", "<J01> F safe"])
def test_prefix_other_than_jk_is_rejected(formula):
    """A coalition `<2>`, no prefix, or a budget with a leading zero is not OL."""
    assert OLParser().parse(formula, n_agent=1) is None


@pytest.mark.unit
def test_leading_zero_bound_is_named():
    """`<J01>` is refused with a message that names it, not as a stray `<`."""
    parser = OLParser()
    assert parser.parse("<J01> F safe", n_agent=1) is None
    assert parser.errors == ["Bound '<J01>' has a leading zero; write <J1>"]


@pytest.mark.unit
def test_budget_zero_is_valid():
    """ECAI 2023 takes the grade n in N0, so the Demon may have no budget."""
    assert OLParser().parse("<J0> F safe", n_agent=1) == ("<J0>F", "safe")
