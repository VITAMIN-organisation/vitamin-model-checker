"""Formula parsers accept uppercase atomic proposition names."""

import pytest

from model_checker.parsers.formulas.CTL.parser import CTLParser
from model_checker.parsers.formulas.LTL.parser import LTLParser
from model_checker.parsers.formulas.NatATL.parser import NatATLParser


@pytest.mark.unit
@pytest.mark.parametrize(
    "parser_cls, formula, expected",
    [
        (CTLParser, "EF Goal", ("EF", "Goal")),
        (CTLParser, "AG safe", ("AG", "safe")),
        (LTLParser, "F Goal", ("F", "Goal")),
        (LTLParser, "G safe", ("G", "safe")),
    ],
)
def test_uppercase_atomic_proposition_parses(parser_cls, formula, expected):
    parser = parser_cls()
    assert parser.parse(formula) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula,expected",
    [
        ("Goal", "Goal"),
        ("<{1},5>F Goal", ("<{1},5>F", "Goal")),
        ("<{1},5>F Flag", ("<{1},5>F", "Flag")),
    ],
)
def test_natatl_bare_and_modal_uppercase_propositions(formula, expected):
    assert NatATLParser().parse(formula, n_agent=1) == expected


@pytest.mark.unit
def test_ltl_rejects_reserved_word_proposition():
    assert LTLParser().parse("F forall") is None
    assert LTLParser().parse("forall") is None
