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


# logic -> binary operators it has (NatSL's one goal has none)
_BINARY_OPERATORS = {
    "LTL": ("U",),
    "CTL": ("U",),
    "ICTL": ("U", "R"),
    "TCTL": ("U",),
    "ATL": ("U",),
    "ATLF": ("U",),
    "IATL": ("U", "R"),
    "ATL_STAR": ("U",),
    "Wallet_ATL": ("U",),
    "OATL": ("U", "R", "W"),
    "COTL": ("U", "R", "W"),
    "RBATL": ("U",),
    "RABATL": ("U",),
    "NatATL": ("U",),
    "NatATL_Recall": ("U",),
    "NatATLF": ("U",),
    "CapATL": ("U", "R"),
    "OL": ("U", "R", "W"),
    "TOL": ("U", "R", "W"),
    "NatSL": (),
}

# The CTL family writes a binary operator inside the path quantifier's brackets.
_BINARY_WRAP = {"CTL": "A[{}]", "ICTL": "A[{}]", "TCTL": "A({})"}

_BINARY_CASES = sorted(
    (logic, op) for logic, ops in _BINARY_OPERATORS.items() for op in ops
)


def _binary(logic: str, body: str) -> str:
    """Put a binary body such as `p U q` after the logic's prefix, or inside its brackets."""
    if logic in _BINARY_WRAP:
        return _BINARY_WRAP[logic].format(body)
    return f"{_OPERATOR_FORMS[logic][0]}{body}"


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
    for name, table in (
        ("_OPERATOR_FORMS", _OPERATOR_FORMS),
        ("_BINARY_OPERATORS", _BINARY_OPERATORS),
    ):
        assert registered == set(table), (
            f"{name} differs from the registered logics: add {sorted(registered - set(table))}, "
            f"remove {sorted(set(table) - registered)}. Each logic must read an operator "
            "as a word of its own."
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "op"),
    sorted(
        (logic, op)
        for logic in _OPERATOR_FORMS
        for op in "URW"
        if op not in _BINARY_OPERATORS[logic]
    ),
)
def test_binary_operator_table_lists_every_operator_the_logic_accepts(logic, op):
    """A logic that gains R or W must be added to _BINARY_OPERATORS, or its glued forms go untested."""
    text = _binary(logic, f"p {op} q")
    assert (
        _parse(logic, text) is None
    ), f"{logic} accepts '{text}': add {op} to the table"


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


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "op"), _BINARY_CASES)
def test_binary_operator_apart_from_its_names_is_accepted(logic, op):
    for left, right in (("p", "q"), ("Fuel", "Goal")):
        text = _binary(logic, f"{left} {op} {right}")
        result = _parse(logic, text)
        assert result is not None, f"{logic} rejected '{text}'"
        assert _holds_word(result, left) and _holds_word(
            result, right
        ), f"{logic} lost a name of '{text}'"


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "op"), _BINARY_CASES)
@pytest.mark.parametrize(
    ("body", "glued"),
    [("p{op}q", "p{op}q"), ("p{op} q", "p{op}"), ("p {op}q", "{op}q")],
)
def test_binary_operator_glued_to_a_name_is_never_an_operator(logic, op, body, glued):
    """`pUq` is one name; `pU q` and `p Uq` are rejected, never split at the operator."""
    text = _binary(logic, body.format(op=op))
    result = _parse(logic, text)
    word = glued.format(op=op)
    assert result is None or _holds_word(
        result, word
    ), f"{logic} read '{text}' as {result!r}; it must be rejected or keep '{word}'"


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_OPERATOR_FORMS))
def test_lowercase_unary_operator_is_rejected(logic):
    prefix, op = _OPERATOR_FORMS[logic]
    assert (
        _parse(logic, f"{prefix}{op.lower()} p") is None
    ), f"{logic} accepted '{prefix}{op.lower()} p'; operators are uppercase only"


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "op"), _BINARY_CASES)
def test_lowercase_binary_operator_is_rejected(logic, op):
    text = _binary(logic, f"p {op.lower()} q")
    assert (
        _parse(logic, text) is None
    ), f"{logic} accepted '{text}'; operators are uppercase only"
