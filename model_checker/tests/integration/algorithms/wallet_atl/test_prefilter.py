"""Tests for Wallet_ATL early-fail ATL prefilter."""

from unittest.mock import patch

import pytest

from model_checker.algorithms.explicit.Wallet_ATL.Wallet_ATL import (
    _core_walletatl_checking,
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
def test_wallet_atl_short_circuits_on_false_atl(wallet_atl_model):
    """
    If the unconstrained ATL formula evaluates to False, Wallet_ATL should return
    early and not call the expensive explicit solve_tree.
    In wallet_1agent_2states.txt, `<<1>> G q` is False in standard ATL.
    """
    formula = "<< 1 : wallet(1, >= 10) >> G q"

    with patch(
        "model_checker.algorithms.explicit.Wallet_ATL.Wallet_ATL.solve_tree"
    ) as mock_solve_tree:
        result = _core_walletatl_checking(wallet_atl_model, formula)
        assert "error" not in result
        mock_solve_tree.assert_not_called()
        init = str(result.get("initial_state", ""))
        assert ": False" in init
        states = extract_states_from_result(result)
        assert states == {"s1"}


@pytest.mark.unit
@pytest.mark.model_checking
def test_wallet_atl_proceeds_on_true_atl(wallet_atl_model):
    """
    If the unconstrained ATL formula evaluates to True, Wallet_ATL should NOT short-circuit
    and should call solve_tree to verify the wallet constraints.
    In wallet_1agent_2states.txt, `<<1>> F q` is True.
    """
    formula = "<< 1 : wallet(1, >= 10) >> F q"

    with patch(
        "model_checker.algorithms.explicit.Wallet_ATL.Wallet_ATL.solve_tree"
    ) as mock_solve_tree:
        result = _core_walletatl_checking(wallet_atl_model, formula)
        mock_solve_tree.assert_called_once()
