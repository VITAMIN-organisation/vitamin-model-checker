"""Connectives are `&&`, `||`, `!`, `->` or the words `and`, `or`, `not`, `implies` in every logic.

`&`, `|` and `>` are rejected everywhere, so one text is never valid in one logic
and invalid in another (CLAUDE.md, "Syntax rules").
"""

import re

import pytest

from model_checker.tests.helpers.formula_cases import CONNECTIVE_LOGICS, parse, unary

_WORDS = [("(p and q)", "and", "&&"), ("(p or q)", "or", "||")]
_WORDS += [("(p implies q)", "implies", "->"), ("(not p)", "not", "!")]


@pytest.mark.unit
@pytest.mark.parametrize("logic", CONNECTIVE_LOGICS)
@pytest.mark.parametrize(("operand", "word", "symbol"), _WORDS)
def test_word_connective_builds_the_symbol_tree(logic, operand, word, symbol):
    """`p and q` has the tree of `p && q`; most parsers keep the word as the node label."""
    spelled = parse(logic, unary(logic, operand))
    assert spelled is not None, f"{logic} rejected '{word}'"
    expected = parse(logic, unary(logic, operand.replace(f"{word} ", symbol + " ")))
    assert re.sub(rf"\b{word}\b", symbol, repr(spelled)) == repr(expected)


@pytest.mark.unit
@pytest.mark.parametrize("logic", CONNECTIVE_LOGICS)
@pytest.mark.parametrize("symbol", ["&", "|", ">"])
def test_symbol_aliases_are_rejected(logic, symbol):
    """`p & q`, `p | q` and `p > q` are errors, not connectives."""
    text = unary(logic, f"(p {symbol} q)")
    assert parse(logic, text) is None, f"{logic} accepted '{text}'"
