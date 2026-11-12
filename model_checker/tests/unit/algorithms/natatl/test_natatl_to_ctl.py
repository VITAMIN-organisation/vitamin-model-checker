"""NatATL to CTL translation: the solver checks `<{A}, k>F p` as `A F p` with A's strategies of size k."""

import pytest

from model_checker.algorithms.explicit.NatATL.natatl_ast import analyze_natatl_formula
from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import (
    get_agents_from_natatl,
    get_k_value,
    natatl_to_ctl,
)


@pytest.mark.unit
def test_translation_keeps_operator_agents_and_bound():
    """The CTL text, the coalition and k all come from the one prefix."""
    formula = "<{1,2}, 5>F p"
    assert natatl_to_ctl(formula, n_agent=2) == "A F p"
    assert get_agents_from_natatl(formula, n_agent=2) == [1, 2]
    assert get_k_value(formula, n_agent=2) == 5


@pytest.mark.unit
@pytest.mark.parametrize(
    ("word", "symbol"), [("and", "&&"), ("or", "||"), ("implies", "->")]
)
@pytest.mark.parametrize(
    "template", ["(<{{1}},1>F p) {} (<{{2}},3>G q)", "p {} <{{2}},3>F q"]
)
def test_word_connective_translates_like_its_symbol(template, word, symbol):
    """`and` gives the same CTL text, agents and k as `&&`, and CTL parses the text
    (`analyze_natatl_formula` raises otherwise)."""
    spelled = analyze_natatl_formula(template.format(word), n_agent=2)
    symbolic = analyze_natatl_formula(template.format(symbol), n_agent=2)
    assert spelled[1:] == symbolic[1:]


@pytest.mark.unit
def test_connective_operands_are_parenthesized():
    """CTL refuses `A F p && A G q` as ambiguous, so each side gets parentheses."""
    _, ctl, _, _ = analyze_natatl_formula("(<{1},1>F p) && (<{2},3>G q)", n_agent=2)
    assert ctl == "((A F p) && (A G q))"


@pytest.mark.unit
def test_name_starting_with_an_operator_letter_is_refused_whole():
    """`Fuel` is refused as one name, not read as `F uel`."""
    with pytest.raises(ValueError, match="Atomic proposition 'Fuel'"):
        natatl_to_ctl("<{1},1>F Fuel")


@pytest.mark.unit
def test_operator_glued_to_a_name_is_rejected():
    """`Fa` is one name, so `<{1},1>Fa` has no operator."""
    with pytest.raises(ValueError, match="Invalid NatATL formula"):
        natatl_to_ctl("<{1},1>Fa")


@pytest.mark.unit
@pytest.mark.parametrize(
    "convert", [natatl_to_ctl, get_k_value, get_agents_from_natatl]
)
def test_formula_without_a_bound_is_rejected(convert):
    """`<1,2>F p` has no k, so no translation exists."""
    with pytest.raises(ValueError):
        convert("<1,2>F p")
