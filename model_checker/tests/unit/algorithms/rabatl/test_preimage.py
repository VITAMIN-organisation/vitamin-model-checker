"""RABATL pre-image: pre() for resource-aware bounded one-step forcing."""

import pytest

from model_checker.algorithms.explicit.RABATL.preimage import pre
from model_checker.tests.helpers.model_helpers import load_test_model


@pytest.mark.unit
@pytest.mark.model_checking
class TestRABATLPreImage:
    """Test RABATL pre() function."""

    def test_pre_returns_subset_of_states(self, test_data_dir):
        """pre() returns a set of state names contained in the model states."""
        cgs = load_test_model(
            test_data_dir, "costCGS/RABATL/rabatl_3agents_medium_6states_costs.txt"
        )
        all_states = set(cgs.get_states())
        result = pre(cgs, "1", {"s1"}, [10, 10, 10])
        assert isinstance(result, set)
        assert all(isinstance(s, str) for s in result)
        assert result <= all_states
