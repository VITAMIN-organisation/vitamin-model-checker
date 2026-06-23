"""CTL pre-validation and bare proposition parsing."""

import pytest

from model_checker.parsers.formulas.CTL.parser import CTLParser


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "Goal",
        "Flux",
        "Xray",
        "safe",
        "using",
    ],
)
def test_ctl_accepts_bare_propositions_with_modal_letters(formula):
    assert CTLParser().parse(formula) == formula


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "F p",
        "G q",
        "X r",
        "U p q",
    ],
)
def test_ctl_rejects_unquantified_temporal_operators(formula):
    assert CTLParser().parse(formula) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula,expected",
    [
        ("EF Goal", ("EF", "Goal")),
        ("EF Flag", ("EF", "Flag")),
        ("AG Flux", ("AG", "Flux")),
    ],
)
def test_ctl_quantified_formulas_with_uppercase_propositions(formula, expected):
    assert CTLParser().parse(formula) == expected


@pytest.mark.unit
def test_ctl_rejects_reserved_word_proposition():
    assert CTLParser().parse("EF forall") is None
