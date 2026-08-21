"""RBATL pre-image: compute_pre_states for resource-bounded one-step forcing."""

import pytest

from model_checker.algorithms.explicit.shared.bounded_atl_preimage import (
    build_transition_cache,
    compute_pre_states,
)
from model_checker.tests.helpers.model_helpers import load_test_model


@pytest.mark.unit
@pytest.mark.model_checking
class TestRBATLPreImage:
    """Exact Pre pins on the medium RBATL cost fixture."""

    def test_pre_forces_only_states_that_cannot_escape_target(self, test_data_dir):
        """From s0, action A|A|^ reaches both s1 and s3, so Pre({s1}) excludes s0."""
        cgs = load_test_model(
            test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
        )
        trans_cache = build_transition_cache(cgs, "1")
        only_s1 = compute_pre_states(
            cgs, "1", {"s1"}, [100, 100, 100], trans_cache, "rbatl"
        )
        s1_and_s3 = compute_pre_states(
            cgs, "1", {"s1", "s3"}, [100, 100, 100], trans_cache, "rbatl"
        )
        assert only_s1 == {"s1"}
        assert s1_and_s3 == {"s0", "s1", "s3"}
        assert "s0" not in only_s1
        assert "s0" in s1_and_s3
