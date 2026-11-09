"""Every logic with a prefix before Until accepts it with and without parentheses.

`prefix p U q` and `prefix (p U q)` are two ways to write one formula: ATL writes
the first (JACM 2002, p. 685), the obstruction and probabilistic papers write the
second, and ATL is the fragment of ATL* in which every temporal operator follows a
path quantifier (p. 689). Both forms must build the same tree.
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
    prefix = PREFIX[logic]
    flat_tree = _tree(logic, flat.format(c=prefix))
    assert flat_tree != "None"
    assert _tree(logic, grouped.format(c=prefix)) == flat_tree


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
def test_grouped_until_is_one_conjunct(logic):
    prefix = PREFIX[logic]
    grouped = _tree(logic, f"({prefix} (p U q)) && r")
    assert grouped != "None"
    assert _tree(logic, f"{prefix} (p U q) && r") == grouped


@pytest.mark.unit
@pytest.mark.parametrize("logic", PREFIX)
@pytest.mark.parametrize("formula", ["{c} (p U)", "{c} (p U q", "{c} p U q)"])
def test_unclosed_until_is_rejected(logic, formula):
    assert _tree(logic, formula.format(c=PREFIX[logic])) == "None"
