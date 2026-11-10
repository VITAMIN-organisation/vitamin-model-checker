"""NatATL to CTL translation: the solver checks `<{A}, k>F p` as `A F p` with A's strategies of size k."""

import pytest

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
def test_name_starting_with_an_operator_letter_is_kept_whole():
    """`Fuel` must reach CTL as one name, not as `F uel`."""
    assert natatl_to_ctl("<{1},1>F Fuel") == "A F Fuel"


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
