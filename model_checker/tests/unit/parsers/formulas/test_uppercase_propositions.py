"""Formula parsers accept uppercase atomic proposition names."""

import pytest

from model_checker.parsers.formulas.CTL.parser import CTLParser
from model_checker.parsers.formulas.LTL.parser import LTLParser


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
