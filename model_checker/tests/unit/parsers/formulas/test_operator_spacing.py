"""A temporal operator is a word of its own in every logic (CLAUDE.md, "Syntax rules").

`F p` applies F to p; `Fp` and `FFuel` are names; `Fuel` and `Goal` are names that
merely start with an operator letter. A logic registered without an entry in the
tables of helpers/formula_cases.py fails the first test, so no logic skips the rule.
"""

from importlib.metadata import entry_points

import pytest

from model_checker.tests.helpers.formula_cases import (
    BINARY_OPERATORS,
    OPERATOR_FORMS,
    binary,
    holds_word,
    parse,
)

_BINARY_CASES = sorted(
    (logic, op) for logic, ops in BINARY_OPERATORS.items() for op in ops
)


@pytest.mark.unit
def test_every_registered_logic_is_covered():
    """A new parser entry point must be added to the tables, or the rules below skip it."""
    registered = {entry.name for entry in entry_points(group="vitamin.parsers")}
    for name, table in (
        ("OPERATOR_FORMS", OPERATOR_FORMS),
        ("BINARY_OPERATORS", BINARY_OPERATORS),
    ):
        assert registered == set(table), (
            f"{name} differs from the registered logics: add {sorted(registered - set(table))}, "
            f"remove {sorted(set(table) - registered)}"
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "op"),
    sorted(
        (logic, op)
        for logic in OPERATOR_FORMS
        for op in "URW"
        if op not in BINARY_OPERATORS[logic]
    ),
)
def test_binary_operator_table_lists_every_operator_the_logic_accepts(logic, op):
    """A logic that gains R or W must be listed, or its glued forms go untested."""
    text = binary(logic, f"p {op} q")
    assert (
        parse(logic, text) is None
    ), f"{logic} accepts '{text}': add {op} to the table"


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
def test_operator_and_name_apart_is_accepted(logic):
    """`F p` and `F fuel` parse and keep the name whole."""
    prefix, op = OPERATOR_FORMS[logic]
    for atom in ("p", "fuel"):
        result = parse(logic, f"{prefix}{op} {atom}")
        assert result is not None, f"{logic} rejected '{prefix}{op} {atom}'"
        assert holds_word(result, atom), f"{logic} lost the name {atom}"


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
@pytest.mark.parametrize("atom", ["p", "Fuel", "goal"])
def test_operator_glued_to_a_name_is_never_an_operator(logic, atom):
    """`Fp` is rejected or kept as the one name `Fp`, never split into `F p`."""
    prefix, op = OPERATOR_FORMS[logic]
    glued = f"{op}{atom}"
    result = parse(logic, f"{prefix}{glued}")
    assert result is None or holds_word(
        result, glued
    ), f"{logic} read '{prefix}{glued}' as {result!r}; it must be rejected or one name '{glued}'"


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
def test_operator_without_operand_is_rejected(logic):
    """`<1>F` alone is incomplete in every logic."""
    prefix, op = OPERATOR_FORMS[logic]
    assert parse(logic, f"{prefix}{op}") is None


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "op"), _BINARY_CASES)
def test_binary_operator_apart_from_its_names_is_accepted(logic, op):
    """`p U q` and `fuel U goal` parse and keep both names."""
    for left, right in (("p", "q"), ("fuel", "goal")):
        text = binary(logic, f"{left} {op} {right}")
        result = parse(logic, text)
        assert result is not None, f"{logic} rejected '{text}'"
        assert holds_word(result, left) and holds_word(
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
    text = binary(logic, body.format(op=op))
    result = parse(logic, text)
    word = glued.format(op=op)
    assert result is None or holds_word(
        result, word
    ), f"{logic} read '{text}' as {result!r}; it must be rejected or keep '{word}'"


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "op"), _BINARY_CASES)
def test_binary_operator_without_right_operand_is_rejected(logic, op):
    """`p U` with nothing after it is incomplete."""
    assert parse(logic, binary(logic, f"p {op}")) is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(OPERATOR_FORMS))
def test_lowercase_unary_operator_is_rejected(logic):
    """Operators are uppercase only: `f p` is not `F p`."""
    prefix, op = OPERATOR_FORMS[logic]
    assert (
        parse(logic, f"{prefix}{op.lower()} p") is None
    ), f"{logic} accepted '{prefix}{op.lower()} p'"


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "op"), _BINARY_CASES)
def test_lowercase_binary_operator_is_rejected(logic, op):
    """Operators are uppercase only: `p u q` is not `p U q`."""
    text = binary(logic, f"p {op.lower()} q")
    assert parse(logic, text) is None, f"{logic} accepted '{text}'"
