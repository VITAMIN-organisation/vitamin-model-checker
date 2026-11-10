"""Wallet_ATL integration tests on WalletCGS fixtures."""

import pytest

from model_checker.algorithms.explicit.Wallet_ATL.Wallet_ATL import (
    _core_walletatl_checking,
    _extract_state_name,
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
        assert "error" in result

    def test_nonexistent_atomic_proposition(self, wallet_atl_model):
        result = _core_walletatl_checking(wallet_atl_model, "<<1>>F missing")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_extract_state_name_strips_wallet_suffixes_only(self):
        assert _extract_state_name("s9:10:20") == "s9"
        assert _extract_state_name("locA:5") == "locA"
        assert _extract_state_name("s_init") == "s_init"
        assert _extract_state_name("s0") == "s0"


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
            ("<<1>>X q", {"s0", "s1"}, True),
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

    def test_wallet_guard_filters_states_by_balance(self, wallet_atl_model):
        """Static guards use Wallets balances (both states have 5 on this fixture)."""
        ok = _core_walletatl_checking(wallet_atl_model, "<<1:wallet(1, >= 5)>>F q")
        assert "error" not in ok, ok
        assert extract_states_from_result(ok) == {"s0", "s1"}

        blocked = _core_walletatl_checking(
            wallet_atl_model, "<<1:wallet(1, >= 10)>>F q"
        )
        assert "error" not in blocked, blocked
        assert extract_states_from_result(blocked) == set()

    def test_wallet_until_applies_guards(self, wallet_atl_model):
        """Until must filter both operands with wallet constraints, like F/X/G."""
        unconstrained = _core_walletatl_checking(wallet_atl_model, "<<1>> p U q")
        assert "error" not in unconstrained, unconstrained
        assert extract_states_from_result(unconstrained) == {"s0", "s1"}

        allowed = _core_walletatl_checking(
            wallet_atl_model, "<<1:wallet(1, >= 5)>> p U q"
        )
        assert "error" not in allowed, allowed
        assert extract_states_from_result(allowed) == {"s0", "s1"}

        blocked = _core_walletatl_checking(
            wallet_atl_model, "<<1:wallet(1, >= 10)>> p U q"
        )
        assert "error" not in blocked, blocked
        assert extract_states_from_result(blocked) == set()


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestWalletATLResultSet:
    """`res` is the exact state set, also when the initial state is False."""

    def test_guard_no_state_satisfies_gives_empty_set(self, wallet_atl_model):
        """Wallets are s0: 5 and s1: 5, so no state meets wallet >= 10 and the set is empty.

        Plain ATL `<1>G q` holds at s1 (q holds there and s1 loops), so an ATL
        result would wrongly list s1.
        """
        result = _core_walletatl_checking(
            wallet_atl_model, "<< 1 : wallet(1, >= 10) >> G q"
        )
        assert "error" not in result
        assert extract_states_from_result(result) == set()
        assert ": False" in result["initial_state"]

    def test_guard_every_state_satisfies_keeps_the_atl_set(self, wallet_atl_model):
        """With wallet >= 0 every state passes the guard, so the set is the ATL one: s1."""
        result = _core_walletatl_checking(
            wallet_atl_model, "<< 1 : wallet(1, >= 0) >> G q"
        )
        assert extract_states_from_result(result) == {"s1"}
