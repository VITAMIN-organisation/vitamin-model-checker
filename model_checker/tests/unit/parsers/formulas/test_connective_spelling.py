"""Every logic spells the connectives one way: `&&`, `||`, `!`, `->` or the words.

`&`, `|` and `>` are not connectives in any logic: a formula that uses one is
rejected, so the same text is never valid in one logic and invalid in another.
NatSL goals take no connectives, so NatSL is not in the table.
"""

import pytest

from .test_operator_spacing import _OPERATOR_FORMS, _parse

_LOGICS = sorted(set(_OPERATOR_FORMS) - {"NatSL"})


def _formula(logic: str, left_to_right: str) -> str:
    prefix, op = _OPERATOR_FORMS[logic]
    return f"{prefix}{op} (p {left_to_right} q)"


@pytest.mark.unit
@pytest.mark.parametrize("logic", _LOGICS)
@pytest.mark.parametrize("connective", ["&&", "||", "->", "and", "or", "implies"])
def test_canonical_and_word_connectives_are_accepted(logic, connective):
    text = _formula(logic, connective)

    assert _parse(logic, text) is not None, f"{logic} rejected '{text}'"


@pytest.mark.unit
@pytest.mark.parametrize("logic", _LOGICS)
@pytest.mark.parametrize("symbol", ["&", "|", ">"])
def test_symbol_aliases_are_rejected(logic, symbol):
    text = _formula(logic, symbol)

    assert _parse(logic, text) is None, f"{logic} accepted '{text}'"
