"""Which words are proposition names, in every logic.

A name starts with a letter and may start with an operator letter (`Apple`, `Xray`).
The reserved words of docs/logic_knowledge_base.md ("Reserved keywords") are never
names, and the word forms of the operators (`eventually`, `until`) are operators.
"""

import pytest

from model_checker.parsers.syntax_patterns import FORMULA_RESERVED_WORDS
from model_checker.tests.helpers.formula_cases import (
    BINARY_OPERATORS,
    OPERATOR_FORMS,
    binary,
    holds_word,
    parse,
)

# docs/logic_knowledge_base.md, "Reserved keywords (case-insensitive)"
_DOCUMENTED_RESERVED = {
    "and",
    "or",
    "not",
    "implies",
    "until",
    "release",
    "globally",
    "next",
    "eventually",
    "always",
    "forall",
    "exist",
    "true",
    "false",
}

# Reserved as names, but in a formula they are valid constants.
_CONSTANTS = {"true", "false"}

# Parsers that still read these reserved words as names (a known bug, not the rule).
_STILL_ACCEPTED = {
    "TCTL": {"release"},
    "ATL_STAR": {"always", "exist", "forall", "release"},
    "TOL": {"exist", "forall", "release"},
    "NatSL": {"always", "globally", "implies", "next", "or", "release", "until"},
}

_RESERVED_CASES = sorted(
    (logic, word)
    for logic in OPERATOR_FORMS
    for word in _DOCUMENTED_RESERVED - _CONSTANTS - _STILL_ACCEPTED.get(logic, set())
)


@pytest.mark.unit
def test_reserved_words_match_the_docs():
    """The parser's list and the documented list are the same fourteen words."""
    assert FORMULA_RESERVED_WORDS == _DOCUMENTED_RESERVED


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "word"), _RESERVED_CASES)
def test_reserved_word_is_not_a_proposition(logic, word):
    """`F forall` is an error: a reserved word cannot name a proposition."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} {word}") is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
@pytest.mark.parametrize(
    "name",
    ["Apple", "Error", "Red", "Water", "Knowledge", "Xray", "nextstate", "p_X"],
)
def test_name_starting_with_an_operator_letter_is_a_proposition(logic, name):
    """A, E, R, W, K and X start names too; the lexer must not split them off."""
    prefix, op = OPERATOR_FORMS[logic]
    result = parse(logic, f"{prefix}{op} {name}")
    assert result is not None and holds_word(result, name), result


# Wallet_ATL still rejects `true` and `false` in a formula (not yet decided).
@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(set(OPERATOR_FORMS) - {"Wallet_ATL"}))
@pytest.mark.parametrize("constant", sorted(_CONSTANTS))
def test_reserved_constant_is_accepted_as_a_constant_in_a_formula(logic, constant):
    """`F true` parses: `true` and `false` are reserved as names but are valid constants."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} {constant}") is not None


@pytest.mark.unit
# Wallet_ATL rejects the constants altogether; NatSL, TCTL and TOL do not refuse reserved
# words as names in a formula (see _STILL_ACCEPTED). The solver then reports the name as
# undeclared, since a model cannot declare it.
@pytest.mark.parametrize(
    "logic", sorted(set(OPERATOR_FORMS) - {"Wallet_ATL", "NatSL", "TCTL", "TOL"})
)
def test_constant_in_another_letter_case_is_never_a_proposition(logic):
    """`True` is refused as a name; ATL_STAR's lexer reads it as the constant instead."""
    prefix, op = OPERATOR_FORMS[logic]
    result = parse(logic, f"{prefix}{op} True")
    assert result is None or not holds_word(result, "True"), result


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
def test_name_with_a_leading_digit_is_rejected(logic):
    """`1goal` is not an identifier."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} 1goal") is None


# NatSL goals take F, G and X only. TCTL has no next; ATL* has no `always` (known bug).
_WORD_OPERATOR_CASES = sorted(
    (logic, word, symbol)
    for logic in OPERATOR_FORMS
    if logic != "NatSL"
    for word, symbol in [
        ("eventually", "F"),
        ("globally", "G"),
        ("always", "G"),
        ("next", "X"),
    ]
    if not (logic == "TCTL" and word == "next")
    and not (logic == "ATL_STAR" and word == "always")
)


def _quantified(logic: str, op: str) -> str:
    """The prefix for a unary operator: the CTL family writes `A F p` as `A` and `F`."""
    prefix, default = OPERATOR_FORMS[logic]
    if default == "AF":
        return f"A {op}"
    return f"{prefix}{op}"


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "word", "symbol"), _WORD_OPERATOR_CASES)
def test_word_operator_builds_the_symbol_tree(logic, word, symbol):
    """`eventually p` is `F p`."""
    # repr, because the TCTL and TOL nodes do not define equality.
    spelled = parse(logic, f"{_quantified(logic, word)} p")
    assert spelled is not None, f"{logic} rejected '{word}'"
    assert repr(spelled) == repr(parse(logic, f"{_quantified(logic, symbol)} p"))


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic", sorted(logic for logic, ops in BINARY_OPERATORS.items() if "U" in ops)
)
def test_until_word_builds_the_symbol_tree(logic):
    """`p until q` is `p U q`."""
    spelled = parse(logic, binary(logic, "p until q"))
    assert spelled is not None, f"{logic} rejected 'until'"
    assert repr(spelled) == repr(parse(logic, binary(logic, "p U q")))
