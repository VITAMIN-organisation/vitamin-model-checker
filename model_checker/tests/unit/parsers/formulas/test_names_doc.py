"""The KB sections "Names and keywords" and "Syntax cards" against the code.

docs/reference/logic_knowledge_base.md is the one doc that states the reserved words, the word
operators and a syntax card per logic. These tests read its tables, so a change to
`OPERATOR_WORDS`, `FORMULA_RESERVED_WORDS`, a parser or a logic's model type that
the doc does not follow fails here. The KB lives outside the package, so these tests
run from a source checkout only.
"""

import re
from pathlib import Path

import pytest

from model_checker.parsers.syntax_patterns import (
    FORMULA_RESERVED_WORDS,
    OPERATOR_WORDS,
)
from model_checker.registries import get_expected_model_type
from model_checker.tests.helpers.formula_cases import (
    OPERATOR_FORMS,
    binary,
    negated,
    parse,
    quantified,
    unary,
)

_KB = Path(__file__).resolve().parents[5] / "docs" / "reference" / "logic_knowledge_base.md"
_EXCEPT = "every logic except "


def _section(text: str, heading: str, level: str) -> str:
    """The body under `level heading` up to the next heading of that level or above.

    The KB sections read here hold no fenced line starting with `#`, which would end
    the section early."""
    match = re.search(
        rf"^{level} {re.escape(heading)}\n(.*?)(?=^#{{1,{len(level)}}} |\Z)",
        text,
        re.M | re.S,
    )
    assert match, f"{_KB.name} has no heading {level} {heading!r}"
    return match.group(1)


_KB_TEXT = _KB.read_text(encoding="utf-8")
_NAMES = _section(_KB_TEXT, "Names and keywords", "##")


def _table(body: str) -> list[list[str]]:
    """The body rows of the one pipe table in `body`, cells without backticks."""
    lines = [line for line in body.splitlines() if line.startswith("|")]
    assert len(lines) > 2, "no table in the section"
    return [
        [
            cell.strip().replace("\\|", "|").strip("`")
            for cell in re.split(r"(?<!\\)\|", line)[1:-1]
        ]
        for line in lines[2:]
    ]


def _logics_in(cell: str) -> set[str]:
    """`every logic`, `every logic except A, B` or a list `A, B` as a set of logics."""
    if cell == "every logic":
        return set(OPERATOR_FORMS)
    if cell.startswith(_EXCEPT):
        return set(OPERATOR_FORMS) - set(cell.removeprefix(_EXCEPT).split(", "))
    return set(cell.split(", "))


@pytest.mark.unit
def test_reserved_words_match_the_docs():
    """The reserved-words line lists `FORMULA_RESERVED_WORDS`, no more and no fewer."""
    line = next(
        line
        for line in _NAMES.splitlines()
        if line.startswith("Reserved words (any letter case):")
    )
    assert set(re.findall(r"`([^`]+)`", line)) == FORMULA_RESERVED_WORDS


_WORD_ROWS = _table(_section(_NAMES, "Word operators", "###"))


@pytest.mark.unit
def test_word_table_matches_operator_words():
    """The word table has one row per word of `OPERATOR_WORDS`, with its symbol."""
    documented = {word: symbol for word, symbol, _ in _WORD_ROWS}
    in_code = {
        word: row.symbol for row in OPERATOR_WORDS.values() for word in row.words
    }
    assert documented == in_code


_TOKEN_OF = {
    spelling: token
    for token, row in OPERATOR_WORDS.items()
    for spelling in (row.symbol, *row.words)
}
# The connective words stay as written in the PLY parse trees (`('and', 'p', 'q')`).
_KEPT_AS_WRITTEN = {"NOT", "AND", "OR", "IMPLIES"}


def _probe(logic: str, spelling: str) -> str:
    """A formula of `logic` that uses `spelling` (a word or its symbol) as its operator.

    Outside the logics that read `forall`, `exist`, `with` or `is`, the formula also
    fails for want of the operator itself; that every word is reserved in every
    logic is checked in test_proposition_names.py."""
    token = _TOKEN_OF[spelling]
    if token == "NOT":
        return negated(logic, spelling)
    if token in ("AND", "OR", "IMPLIES"):
        return unary(logic, f"(p {spelling} q)")
    if token in ("NEXT", "EVENTUALLY", "GLOBALLY"):
        return quantified(logic, spelling, "p")
    if token in ("UNTIL", "RELEASE", "WEAK"):
        return binary(logic, f"p {spelling} q")
    if token in ("FORALL", "EXIST"):
        return f"{spelling} F p"
    if token == "TIME_SEP":
        return unary(logic, f"(p {spelling} x<5)")
    if token == "IS":
        return f"K1(1 {spelling} c)"
    raise ValueError(f"no probe for operator token {token!r} ({spelling!r})")


_READ_BY = sorted(
    (word, symbol, logic, logic in _logics_in(read_by))
    for word, symbol, read_by in _WORD_ROWS
    for logic in OPERATOR_FORMS
)


@pytest.mark.unit
@pytest.mark.parametrize(("word", "symbol", "logic", "reads"), _READ_BY)
def test_word_is_read_by_the_logics_the_docs_name(word, symbol, logic, reads):
    """A word parses in the logics of its "Read by" cell, where it builds the tree of
    its symbol (`eventually p` is `F p`), and is an error elsewhere."""
    spelled = parse(logic, _probe(logic, word))
    assert (spelled is not None) == reads, f"{logic}: {_probe(logic, word)!r}"
    if reads and _TOKEN_OF[word] not in _KEPT_AS_WRITTEN:
        # repr, because the TCTL and TOL nodes do not define equality.
        assert repr(spelled) == repr(parse(logic, _probe(logic, symbol)))


_CARDS = _table(_section(_KB_TEXT, "Syntax cards", "##"))


@pytest.mark.unit
def test_syntax_cards_cover_every_logic():
    assert sorted(logic for logic, *_ in _CARDS) == sorted(OPERATOR_FORMS)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "model", "example"),
    [(logic, model, example) for logic, _, _, model, example in _CARDS],
)
def test_syntax_card_matches_the_logic(logic, model, example):
    """The card's example parses and its model type is the registry's."""
    assert parse(logic, example) is not None, f"{logic} rejected {example!r}"
    assert get_expected_model_type(logic) == model
