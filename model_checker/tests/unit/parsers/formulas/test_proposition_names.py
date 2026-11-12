"""Which words are proposition names, in every logic.

A name starts with a lowercase letter (`goal`, `gOAL`); `Goal` and `P` are errors.
The reserved words (docs/reference/logic_knowledge_base.md, "Names and keywords", checked
against `FORMULA_RESERVED_WORDS` by test_names_doc.py) are never names, and the word
forms of the operators (`eventually`, `until`) are operators.
"""

import pytest

from model_checker.parsers.syntax_patterns import (
    BOOLEAN_CONSTANTS,
    FORMULA_RESERVED_WORDS,
)
from model_checker.tests.helpers.formula_cases import (
    OPERATOR_FORMS,
    holds_word,
    parse,
    parse_errors,
    unary,
)

# The constants are reserved as names, but in a formula they are valid constants.
_RESERVED_CASES = sorted(
    (logic, word)
    for logic in OPERATOR_FORMS
    for word in FORMULA_RESERVED_WORDS - BOOLEAN_CONSTANTS
)


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "word"), _RESERVED_CASES)
def test_reserved_word_is_not_a_proposition(logic, word):
    """`F forall` is an error: a reserved word cannot name a proposition."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} {word}") is None


# The constants are included: `True` is neither a name nor the constant `true`.
_RESERVED_IN_OTHER_CASE = sorted(
    (logic, spelling)
    for logic in OPERATOR_FORMS
    for word in FORMULA_RESERVED_WORDS
    for spelling in (word.capitalize(), word.upper())
)


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "word"), _RESERVED_IN_OTHER_CASE)
def test_reserved_word_in_another_letter_case_is_not_a_proposition(logic, word):
    """`F Globally` is an error: reserved words are case-insensitive as names
    (docs/reference/logic_knowledge_base.md, "Names and keywords", rule 2)."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} {word}") is None


@pytest.mark.unit
# NatSL reports errors by raising ValueError.
@pytest.mark.parametrize("logic", sorted(set(OPERATOR_FORMS) - {"NatSL"}))
def test_refused_name_is_named_in_the_errors(logic):
    """`F Globally` is refused with a reason that names `Globally`, not an empty list."""
    # `globally` is reserved in any letter case (KB "Names and keywords").
    errors = parse_errors(logic, unary(logic, "Globally"))
    assert any("'Globally'" in error for error in errors), errors


@pytest.mark.unit
# `Next` is reserved in any letter case (KB "Names and keywords"); `Goal` starts
# with a capital.
@pytest.mark.parametrize("name", ["Next", "Goal"])
@pytest.mark.parametrize(
    "logic, formula, kind",
    [
        ("CapATL", "K1(1 is {})", "Capacity"),
        ("TCTL", "AF p : {}<=2", "Clock"),
        ("TCTL", "{}.AF p", "Clock"),
        ("TOL", "{{J1}}F p : {}<=2", "Clock"),
        ("TOL", "{{J1}}F p with {}<=2", "Clock"),
        ("TOL", "{{J1}}F p : x<=1, {}<=2", "Clock"),
        ("TOL", "{}.{{J1}}F p", "Clock"),
    ],
)
def test_clock_and_capacity_follow_the_name_rule(logic, formula, kind, name):
    """A capacity, or a clock in a freeze or a comparison, is refused by name."""
    errors = parse_errors(logic, formula.format(name))
    assert any(f"{kind} '{name}'" in error for error in errors), errors


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
@pytest.mark.parametrize("name", ["gOAL", "x", "apple", "xray", "nextstate", "p_X"])
def test_name_starting_with_a_lowercase_letter_is_a_proposition(logic, name):
    """A name starts with a lowercase letter; capitals may follow."""
    prefix, op = OPERATOR_FORMS[logic]
    result = parse(logic, f"{prefix}{op} {name}")
    assert result is not None and holds_word(result, name), result


_UPPERCASE_FIRST = ["Goal", "P", "GOAL", "Apple", "Xray"]


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
@pytest.mark.parametrize("name", _UPPERCASE_FIRST)
def test_name_starting_with_an_uppercase_letter_is_refused(logic, name):
    """`F Goal` is an error (naming rule 1): a name starts with a lowercase letter."""
    assert parse(logic, unary(logic, name)) is None


# NatSL raises instead of listing errors. IATL, TCTL and TOL lex only
# `[A-Z][a-z]...` as a word, so that `AF` stays an operator; an all-capital word
# is an invalid character there.
_REFUSED_BY_NAME = sorted(
    (logic, name)
    for logic in set(OPERATOR_FORMS) - {"NatSL"}
    for name in _UPPERCASE_FIRST
    if not (logic in {"IATL", "TCTL", "TOL"} and name.isupper())
)


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "name"), _REFUSED_BY_NAME)
def test_refused_uppercase_name_is_named_in_the_errors(logic, name):
    """`F Goal` is refused with a reason that names `Goal`."""
    errors = parse_errors(logic, unary(logic, name))
    assert any(f"'{name}' is invalid" in error for error in errors), errors


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
@pytest.mark.parametrize("constant", sorted(BOOLEAN_CONSTANTS))
def test_reserved_constant_is_accepted_as_a_constant_in_a_formula(logic, constant):
    """`F true` parses: `true` and `false` are reserved as names but are valid constants."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} {constant}") is not None


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
@pytest.mark.parametrize("name", ["1goal", "_goal"])
def test_name_not_starting_with_a_letter_is_rejected(logic, name):
    """`1goal` and `_goal` are not identifiers: a name starts with a letter."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op} {name}") is None


# Which logic reads which word, and that a word builds its symbol's tree, is
# checked against the KB word table in test_names_doc.py.


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic, formula, word",
    [
        ("OL", "<J1> weak p", "weak"),
        ("LTL", "until p", "until"),
        ("LTL", "F p next", "next"),
    ],
)
def test_syntax_error_names_the_word_as_written(logic, formula, word):
    """`<J1> weak p` names `weak`, not the symbol `W` it is read as."""
    errors = parse_errors(logic, formula)
    assert any(f"near token '{word}'" in error for error in errors), errors


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["a U p", "e U p"])
def test_ctl_name_a_or_e_is_not_a_quantifier(formula):
    """The names `a` and `e` are not the quantifiers `A` and `E` (lowercase `a U p`
    has no quantifier)."""
    errors = parse_errors("CTL", formula)
    assert any("preceded by a path quantifier" in error for error in errors), errors
