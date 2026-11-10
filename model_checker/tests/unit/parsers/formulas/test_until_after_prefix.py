"""How every logic with a prefix (coalition, path quantifier, bound) groups it.

`prefix p U q` and `prefix (p U q)` are two ways to write one formula: ATL writes
the first (JACM 2002, p. 685), the obstruction and probabilistic papers write the
second, and ATL is the fragment of ATL* in which every temporal operator follows a
path quantifier (p. 689). Both forms must build the same tree.

No paper states how `prefix F p && q` or `prefix p U q && r` groups, so both are
syntax errors that ask for parentheses.
"""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory

PREFIX = {
    "ATL": "<1>",
    "ATLF": "<1>",
    "IATL": "<1>",
    "COTL": "<1><2>",
    "OATL": "<1><5>",
    "RBATL": "<1><5>",
    "RABATL": "<1><5,5>",
    "CapATL": "<{1}>",
    "NatATL": "<{1}, 2>",
    "NatATLF": "<{1}, 2>",
    "Wallet_ATL": "<<1>>",
    "ATL_STAR": "<<1>>",
    "OL": "<J5>",
    "TOL": "{J2}",
    "CTL": "A",
    "ICTL": "A",
    "TCTL": "A",
}


def _tree(logic: str, formula: str) -> str:
    parser = FormulaParserFactory.get_parser_instance(logic)
    return repr(parser.parse(formula, n_agent=2))


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
@pytest.mark.parametrize(
    ("flat", "grouped"),
    [
        ("{c} p U q", "{c} (p U q)"),
        ("{c} !p U q", "{c} (!p U q)"),
        ("{c} (p && q) U r", "{c} ((p && q) U r)"),
    ],
)
def test_until_after_the_prefix_is_written_with_or_without_parentheses(
    logic, flat, grouped
):
    """`prefix p U q` and `prefix (p U q)` build one tree."""
    prefix = PREFIX[logic]
    flat_tree = _tree(logic, flat.format(c=prefix))
    assert flat_tree != "None"
    assert _tree(logic, grouped.format(c=prefix)) == flat_tree


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
def test_grouped_until_is_one_conjunct(logic):
    """`prefix (p U q) && r` closes the prefix at the parenthesis."""
    prefix = PREFIX[logic]
    grouped = _tree(logic, f"({prefix} (p U q)) && r")
    assert grouped != "None"
    if logic == "ATL_STAR":
        # <<A>> ((p U q) && r) is an ATL* formula too, so the reading is open.
        assert _tree(logic, f"{prefix} (p U q) && r") == "None"
    else:
        assert _tree(logic, f"{prefix} (p U q) && r") == grouped


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
@pytest.mark.parametrize("formula", ["{c} (p U)", "{c} (p U q", "{c} p U q)"])
def test_unclosed_until_is_rejected(logic, formula):
    """A missing operand or parenthesis around the Until is a syntax error."""
    assert _tree(logic, formula.format(c=PREFIX[logic])) == "None"


def _errors(logic: str, formula: str) -> list[str]:
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(formula, n_agent=2) is None
    return parser.errors


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
@pytest.mark.parametrize(
    "formula",
    [
        "{c}F p && q",
        "{c}G p -> q",
        "{c} p U q && r",
        "{c} p U q || r",
        "!{c}F p && q",
        "q && {c}F p && r",
    ],
)
def test_connective_after_an_open_prefix_is_ambiguous(logic, formula):
    """No paper says how `prefix F p && q` groups, so it asks for parentheses."""
    [error] = _errors(logic, formula.format(c=PREFIX[logic]))
    assert "is ambiguous" in error


@pytest.mark.unit
def test_ambiguity_error_shows_the_prefix_as_written():
    """The message quotes the user's prefix, wallet guard included."""
    [error] = _errors("Wallet_ATL", "<<1: wallet(1, >= 5)>>F p && q")
    assert "(<<1: wallet(1, >= 5)>>F ...) && ..." in error


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
@pytest.mark.parametrize(
    "formula",
    [
        "({c}F p) && q",
        "{c}F (p && q)",
        "({c} p U q) && r",
        "{c} (p U (q && r))",
        "q && {c}F p",
        "!({c}F p) && q",
    ],
)
def test_parenthesized_prefix_parses(logic, formula):
    """Each parenthesized reading of an ambiguous formula is accepted."""
    assert _tree(logic, formula.format(c=PREFIX[logic])) != "None"


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(set(PREFIX) - {"ATL_STAR"}))
def test_left_operand_of_a_prefix_until_has_one_reading(logic):
    """`prefix p` alone is no formula here, so `prefix p && q U r` is `prefix ((p && q) U r)`."""
    prefix = PREFIX[logic]
    flat = _tree(logic, f"{prefix} p && q U r")
    assert flat != "None"
    assert flat == _tree(logic, f"{prefix} ((p && q) U r)")
