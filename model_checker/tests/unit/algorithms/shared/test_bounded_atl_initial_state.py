"""Initial-state satisfaction for bounded ATL solvers."""

import pytest

from model_checker.algorithms.explicit.shared.result_formatters import (
    verify_initial_state,
)


@pytest.mark.unit
class TestBoundedAtlInitialState:
    """verify_initial_state must parse tuple strings, not iterate characters."""

    def test_initial_state_in_tuple_string_result(self):
        assert verify_initial_state("s0", "('s0', 's1')") is True

    def test_initial_state_not_in_tuple_string_result(self):
        assert verify_initial_state("s2", "('s0', 's1')") is False
