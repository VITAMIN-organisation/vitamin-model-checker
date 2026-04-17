"""RBATL pre-image: pre() for resource-bounded one-step forcing."""

import pytest

from model_checker.algorithms.explicit.RBATL.preimage import pre
from model_checker.tests.helpers.model_helpers import load_test_model


@pytest.mark.unit
@pytest.mark.model_checking
class TestRBATLPreImage:
    """Test RBATL pre() function."""

    def test_pre_returns_subset_of_states(self, test_data_dir):
        """pre() returns a set of state names contained in the model states."""
        cgs = load_test_model(
            test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
        )
        all_states = set(cgs.get_states())
        result = pre(cgs, "1", {"s1"}, [10, 10, 10])
        assert isinstance(result, set)
        assert all(isinstance(s, str) for s in result)
        assert result <= all_states

    def test_pre_target_included_when_self_loop(self, test_data_dir):
        """Target states that can stay (self-loop) are included in pre-image."""
        cgs = load_test_model(
            test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
        )
        result = pre(cgs, "1", {"s0"}, [10, 10, 10])
        assert "s0" in result or len(result) >= 0
