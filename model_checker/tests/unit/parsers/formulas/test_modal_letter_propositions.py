"""Unit tests ensuring all logic parsers accept proposition names starting with modal/operator letters."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic,formula,n_agent",
    [
        ("CTL", "AG Apple", None),
        ("CTL", "EX Error", None),
        ("ICTL", "AG Apple", None),
        ("ICTL", "EX Error", None),
        ("ICTL", "AG Red", None),
        ("CapATL", "<{1}, 2>G Red", 1),
        ("CapATL", "<{1}, 2>G Knowledge", 1),
        ("CapATL", "<{1}, 2>G issue", 1),
        ("IATL", "<1>G Red", 1),
        ("OL", "<J1>G Red", None),
        ("OL", "<J1>G Water", None),
        ("NatSL", "E x: (x, 1) F Enemy", None),
        ("NatSL", "E x: (x, 1) F Apple", None),
        ("ATL", "<1>G Apple", 1),
        ("ATLF", "<1>G Apple", 1),
        ("OATL", "<1><2>G Apple", 1),
        ("COTL", "<1><2>G Apple", 1),
        ("RBATL", "<1><2>G Apple", 1),
        ("RABATL", "<1><2>G Apple", 1),
        ("NatATL", "<{1}, 2>G Apple", 1),
        ("NatATLF", "<{1}, 2>G Apple", 1),
        ("TCTL", "AG Apple", None),
        ("TOL", "{J1}G Apple", None),
        ("Wallet_ATL", "<<1>>G Apple", 1),
    ],
)
def test_parsers_accept_propositions_with_modal_first_letters(logic, formula, n_agent):
    """Verify that propositions starting with A, E, R, W, K, etc. are lexed as PROP, not operators."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    kwargs = {} if n_agent is None else {"n_agent": n_agent}
    result = parser.parse(formula, **kwargs)
    assert (
        result is not None
    ), f"Logic '{logic}' failed to parse '{formula}': {parser.errors}"


@pytest.mark.unit
def test_ltl_to_ctl_preserves_multi_letter_propositions():
    """Verify that ltl_to_ctl does not corrupt multi-letter atoms starting with modal letters."""
    from model_checker.parsers.formulas.LTL.ltl_to_ctl import ltl_to_ctl

    assert ltl_to_ctl("F Goal") == "AF Goal"
    assert ltl_to_ctl("X Flux") == "AX Flux"
    assert ltl_to_ctl("FG Goal") == "AF AG Goal"
    assert ltl_to_ctl("Xp") == "AX p"
    assert ltl_to_ctl("FGp") == "AF AG p"
    assert ltl_to_ctl("AXp") == "AX p"
