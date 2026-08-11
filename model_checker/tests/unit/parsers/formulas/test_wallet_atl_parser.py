"""Wallet_ATL parser: coalition prefix and temporal operators after <<>>."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.Wallet_ATL.parser import (
    Wallet_ATLParser,
    do_parsingWallet_ATL,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "<<1>>X p",
        "<<1>> X p",
        "<<1>>F q",
        "<<1,2:wallet(1, >= 50)>>G safe",
    ],
)
def test_wallet_atl_parses_coalition_temporal(formula):
    ast = do_parsingWallet_ATL(formula, max_coalition=2)
    assert ast is not None
    assert ast.get("type") == "coalition_wallet"


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "F p",
        "G q",
        "X p",
        "p U q",
    ],
)
def test_wallet_atl_rejects_bare_temporal_without_coalition(formula):
    assert do_parsingWallet_ATL(formula, max_coalition=2) is None


@pytest.mark.unit
def test_wallet_atl_factory_parse_accepts_wallet_guards():
    """Guards must pass FormulaParserFactory prechecks (colon and '=')."""
    parser = FormulaParserFactory.get_parser_instance("Wallet_ATL")
    ast = parser.parse("<<1:wallet(1, >= 5)>>F q", max_coalition=1)
    assert ast is not None
    assert ast["type"] == "coalition_wallet"
    assert ast["constraints"] == [
        {"agent": 1, "operator": ">=", "value": 5},
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "<<0>>X p",
        "<<1,0>>F q",
        "<<1:wallet(0, >= 5)>>G safe",
    ],
)
def test_wallet_atl_rejects_agent_zero(formula):
    assert do_parsingWallet_ATL(formula, max_coalition=2) is None


@pytest.mark.unit
def test_wallet_atl_post_validation_rejects_malformed_dict_ast():
    parser = Wallet_ATLParser()
    malformed = {
        "type": "coalition_wallet",
        "agents": [1],
        "constraints": [{"agent": 1, "operator": "??", "value": 5}],
        "formula": {"type": "proposition", "proposition": "p"},
    }
    assert parser._post_validation("", malformed) is False


@pytest.mark.unit
def test_wallet_atl_post_validation_accepts_well_formed_dict_ast():
    parser = Wallet_ATLParser()
    well_formed = {
        "type": "coalition_wallet",
        "agents": [1],
        "constraints": [{"agent": 1, "operator": ">=", "value": 5}],
        "formula": {
            "type": "unary",
            "operator": "F",
            "formula": {"type": "proposition", "proposition": "q"},
        },
    }
    assert parser._post_validation("", well_formed) is True
