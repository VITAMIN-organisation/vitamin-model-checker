"""Wallet_ATL parser: coalition prefix and temporal operators after <<>>."""

import pytest

from model_checker.parsers.formulas.Wallet_ATL.parser import do_parsingWallet_ATL


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
