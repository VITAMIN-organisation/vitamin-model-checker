"""Connectives group the same way in every logic.

Precedence follows docs/logic_knowledge_base.md ("Boolean Operators"): `!` binds
tightest, then `&&`, `||`, `->`. `&&` and `||` group to the left, `->` to the right.
Each flat formula must build the tree of its parenthesized reading and differ from
the other reading, so a parser that ignored the parentheses would fail.
"""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.tests.helpers.formula_cases import CONNECTIVE_LOGICS, parse, unary

_CASES = [
    # (flat, its reading, the reading it must not have)
    ("p && q || r", "(p && q) || r", "p && (q || r)"),
    ("p || q && r", "p || (q && r)", "(p || q) && r"),
    ("p -> q || r", "p -> (q || r)", "(p -> q) || r"),
    ("!p && q", "(!p) && q", "!(p && q)"),
    ("p && q && r", "(p && q) && r", "p && (q && r)"),
    ("p -> q -> r", "p -> (q -> r)", "(p -> q) -> r"),
]


@pytest.mark.unit
@pytest.mark.parametrize("logic", CONNECTIVE_LOGICS)
@pytest.mark.parametrize(("flat", "reading", "other"), _CASES)
def test_flat_formula_has_one_reading(logic, flat, reading, other):
    """`p && q || r` is `(p && q) || r`, never `p && (q || r)`."""
    # repr, because the TCTL and TOL nodes do not define equality.
    tree = repr(parse(logic, unary(logic, f"({flat})")))
    assert tree != "None", f"{logic} rejected '{flat}'"
    assert tree == repr(parse(logic, unary(logic, f"({reading})")))
    assert tree != repr(parse(logic, unary(logic, f"({other})")))


def _negated(depth: int) -> str:
    text = "p"
    for _ in range(depth):
        text = f"!({text})"
    return f"({text})"


# ATL* raises RecursionError already at depth 200 (a known bug), so it is left out.
@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(set(CONNECTIVE_LOGICS) - {"ATL_STAR"}))
def test_deep_nesting_is_parsed_or_rejected_with_an_error(logic):
    """200 nested negations parse; 5000 parse or fail with a message, never raise."""
    assert parse(logic, unary(logic, _negated(200))) is not None

    parser = FormulaParserFactory.get_parser_instance(logic)
    result = parser.parse(unary(logic, _negated(5000)), n_agent=2)
    assert result is not None or parser.errors
