"""Every logic reads a temporal operator as a word of its own.

`F p` is an operator applied to `p`. `Fp` is one name, and so is `FFuel`, so no
parser may read either as an operator application. A name that merely starts with
an operator letter (`Fuel`, `Goal`) is a valid proposition. The table below lists
the text before the operator for each logic; a logic registered without an entry
fails `test_every_registered_logic_is_covered`, so a new logic cannot skip the rule.
"""

import re
from importlib.metadata import entry_points

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory

# logic -> (text before the operator, the operator)
_OPERATOR_FORMS = {
    "LTL": ("", "F"),
    "CTL": ("", "AF"),
    "ICTL": ("", "AF"),
    "TCTL": ("", "AF"),
    "ATL": ("<1>", "F"),
    "ATLF": ("<1>", "F"),
    "IATL": ("<1>", "F"),
    "ATL_STAR": ("<<1>> ", "F"),
    "Wallet_ATL": ("<<1>>", "F"),
    "OATL": ("<1><2>", "F"),
    "COTL": ("<1><2>", "F"),
    "RBATL": ("<1><2>", "F"),
    "RABATL": ("<1><2>", "F"),
    "NatATL": ("<{1}, 2>", "F"),
    "NatATL_Recall": ("<{1}, 2>", "F"),
    "NatATLF": ("<{1}, 2>", "F"),
    "CapATL": ("<{1}>", "F"),
    "OL": ("<J1>", "F"),
    "TOL": ("{J1}", "F"),
    "NatSL": ("E{1}x: (x, 1) ", "F"),
}


def _parse(logic: str, text: str):
    """Parse `text`; None when the parser rejects it."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    try:
        return parser.parse(text, n_agent=2)
    except TypeError:
        return parser.parse(text)
    except ValueError:
        return None


def _holds_word(result, word: str) -> bool:
    return re.search(rf"\b{word}\b", repr(result)) is not None


@pytest.mark.unit
def test_every_registered_logic_is_covered():
    registered = {entry.name for entry in entry_points(group="vitamin.parsers")}
    missing = registered - set(_OPERATOR_FORMS)
    assert not missing, (
        f"Add {sorted(missing)} to _OPERATOR_FORMS: each logic must read an operator "
        "as a word of its own."
    )


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_OPERATOR_FORMS))
def test_operator_and_name_apart_is_accepted(logic):
    prefix, op = _OPERATOR_FORMS[logic]
    for atom in ("p", "Fuel"):
        result = _parse(logic, f"{prefix}{op} {atom}")
        assert result is not None, f"{logic} rejected '{prefix}{op} {atom}'"
        assert _holds_word(result, atom), f"{logic} lost the name {atom}"


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_OPERATOR_FORMS))
@pytest.mark.parametrize("atom", ["p", "Fuel", "goal"])
def test_operator_glued_to_a_name_is_never_an_operator(logic, atom):
    """The glued text is rejected or kept whole as a name, never split in two."""
    prefix, op = _OPERATOR_FORMS[logic]
    glued = f"{op}{atom}"
    result = _parse(logic, f"{prefix}{glued}")
    assert result is None or _holds_word(result, glued), (
        f"{logic} read '{prefix}{glued}' as {result!r}; "
        f"it must be rejected or one name '{glued}'"
    )
