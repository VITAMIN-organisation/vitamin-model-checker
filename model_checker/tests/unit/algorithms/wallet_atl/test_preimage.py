"""Wallet_ATL guard filter: a failing guard check is an error, not a False."""

import pytest

from model_checker.algorithms.explicit.Wallet_ATL.preimage import (
    apply_wallet_constraints,
)


class _BrokenWallets:
    def check_wallet_constraint(self, state, agent, condition):
        raise ValueError(f"cannot check agent {agent} at {state}")


@pytest.mark.unit
def test_error_while_checking_a_guard_is_raised():
    """Reading the error as 'guard fails' would drop the state with no message."""
    with pytest.raises(ValueError, match="cannot check agent 1 at s0"):
        apply_wallet_constraints(_BrokenWallets(), [(1, (">=", 5))], {"s0"})
