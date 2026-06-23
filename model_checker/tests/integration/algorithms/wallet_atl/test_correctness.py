"""Wallet_ATL integration tests on WalletCGS fixtures."""

import pytest

from model_checker.algorithms.explicit.Wallet_ATL.Wallet_ATL import (
    _core_walletatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    load_test_model,
)


@pytest.fixture
def wallet_atl_model(test_data_dir):
    """Load wallet_1agent_2states.txt (WalletCGS/WALLET_ATL)."""
    return load_test_model(
        test_data_dir, "WalletCGS/WALLET_ATL/wallet_1agent_2states.txt"
    )


@pytest.mark.unit
@pytest.mark.model_checking
class TestWalletATLErrorHandling:
    """Wallet_ATL rejects invalid inputs."""

    def test_invalid_formula_syntax(self, wallet_atl_model):
        result = model_checking("INVALID_FORMULA", wallet_atl_model.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_nonexistent_atomic_proposition(self, wallet_atl_model):
        result = _core_walletatl_checking(wallet_atl_model, "<<1>>F missing")
        assert "error" in result or "does not exist" in result.get("res", "").lower()


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestWalletATLSemantics:
    """Exact winning states on the minimal WalletCGS fixture."""

    @pytest.mark.parametrize(
        "formula, expected_states, initial_expected",
        [
            ("<<1>>F q", {"s0", "s1"}, True),
            ("<<1>>X p", {"s0"}, True),
            ("<<1>>X q", set(), False),
            ("<<1>>G p", {"s0"}, True),
        ],
    )
    def test_exact_state_sets(
        self, wallet_atl_model, formula, expected_states, initial_expected
    ):
        result = _core_walletatl_checking(wallet_atl_model, formula)
        assert "error" not in result, result
        states = extract_states_from_result(result)
        assert states == expected_states
        init = str(result.get("initial_state", ""))
        assert (": True" in init) is initial_expected
