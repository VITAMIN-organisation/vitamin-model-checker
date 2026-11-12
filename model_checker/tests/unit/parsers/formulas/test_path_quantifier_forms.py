"""CTL, ICTL and TCTL: every temporal operator sits under a path quantifier E or A.

`A p U q`, `A(p U q)` and `A[p U q]` are one formula; square brackets go only
around an Until or Release, and only in CTL and ICTL (Clarke, Emerson, Sistla
1986, p. 246; docs/reference/logic_knowledge_base.md, "Grouping and Nesting").
"""

import pytest

from model_checker.tests.helpers.formula_cases import parse

_CTL_FAMILY = ["CTL", "ICTL", "TCTL"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "op", "tree"),
    [
        ("CTL", "U", "U"),
        ("ICTL", "U", "U"),
        ("ICTL", "R", "R"),
    ],
)
@pytest.mark.parametrize("quantifier", ["A", "E"])
def test_three_written_forms_build_one_tree(logic, op, tree, quantifier):
    """Flat, parenthesized and bracketed forms give the same node, e.g. ('AU', 'p', 'q')."""
    expected = (f"{quantifier}{tree}", "p", "q")
    for text in (
        f"{quantifier} p {op} q",
        f"{quantifier}(p {op} q)",
        f"{quantifier}[p {op} q]",
    ):
        assert parse(logic, text) == expected, text


@pytest.mark.unit
@pytest.mark.parametrize("quantifier", ["A", "E"])
def test_tctl_takes_parentheses_but_no_brackets(quantifier):
    """TCTL writes `A(p U q)`; `A[p U q]` is rejected."""
    flat = parse("TCTL", f"{quantifier} p U q")
    assert flat is not None
    assert repr(parse("TCTL", f"{quantifier}(p U q)")) == repr(flat)
    assert parse("TCTL", f"{quantifier}[p U q]") is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", ["CTL", "ICTL"])
def test_grouped_until_keeps_a_parenthesized_operand(logic):
    """`A((p && q) U r)` puts the conjunction on the left of U."""
    assert parse(logic, "A((p && q) U r)") == ("AU", ("&&", "p", "q"), "r")


@pytest.mark.unit
@pytest.mark.parametrize("logic", _CTL_FAMILY)
@pytest.mark.parametrize("formula", ["F p", "G q", "X r", "p U q", "U p q"])
def test_temporal_operator_without_a_quantifier_is_rejected(logic, formula):
    """`F p` is a path formula, not a CTL state formula."""
    assert parse(logic, formula) is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", _CTL_FAMILY)
@pytest.mark.parametrize(
    "formula", ["A[p && q]", "AF [p]", "A(p U)", "A[p U q)", "A(p U q]"]
)
def test_brackets_only_close_an_until(logic, formula):
    """Brackets around anything but a whole Until, or unmatched ones, are errors."""
    assert parse(logic, formula) is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", _CTL_FAMILY)
@pytest.mark.parametrize("name", ["AF", "EX"])
def test_quantified_operator_is_not_a_name(logic, name):
    """`AG EX` lacks an operand: AF and EX are operators here, unlike in ATL."""
    assert parse(logic, f"AG {name}") is None
